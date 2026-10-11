import io
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from PIL import Image


def node(id, kind="story.prompt", **config):
    return {"id": id, "type": "studio", "position": {"x": 0, "y": 0},
            "data": {"kind": kind, "title": id, "config": config}}


def edge(a, b, output="text", input="text"):
    return {"id": a + b, "source": a, "target": b,
            "sourceHandle": output, "targetHandle": input, "data": {"kind": "data"}}


def png():
    f = io.BytesIO()
    Image.new("RGB", (32, 48), "blue").save(f, "PNG")
    return f.getvalue()


def test_graph_cycle_and_type():
    from app.graph import validate_graph
    ns = [node("a", "image.generate", prompt="x"), node("b", "video.image_to_video", prompt="x")]
    assert not validate_graph(ns, [edge("a", "b", "image", "image")])["errors"]
    assert validate_graph(ns, [edge("b", "a", "video", "image")])["errors"]
    ns = [node("a", "script.expand"), node("b", "script.expand")]
    assert any("循环" in e for e in validate_graph(ns, [edge("a", "b"), edge("b", "a")])["errors"])


def test_selection_and_stable_hash():
    from app.graph import execution_order, snapshot_hash
    ns = [node("a"), node("b", "script.expand"), node("unrelated")]
    assert execution_order(ns, [edge("a", "b")], ["b"]) == ["a", "b"]
    assert snapshot_hash({"a": 1, "b": 2}) == snapshot_hash({"b": 2, "a": 1})
    assert snapshot_hash({"refs": ["v1"]}) != snapshot_hash({"refs": ["v2"]})


def test_build_workflow_without_network():
    from generate_tool.rh_generate_workflow import build_request
    def build(i):
        return build_request("image.generate", {"prompt": str(i)}, {})
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(build, range(8)))
    assert [r["user_data"][0]["fieldValue"] for r in results] == list(map(str, range(8)))
    r = build_request("video.image_to_video", {"prompt": "镜头", "model": "ltx23", "seconds": 5}, {"image": [b"a"]})
    assert r["workflowId"] == "2060724980819775490"
    assert any(v["fieldValue"] == b"a" for v in r["user_data"])
    with pytest.raises(ValueError):
        build_request("image.generate", {"prompt": "x"}, {"image": [b"a"] * 9})


def test_store_reopen_conflict_assets(tmp_path):
    from app.store import Store, Conflict
    s = Store(tmp_path)
    p = s.create_project("测试")
    canvas = s.canvas(p["id"])
    canvas["nodes"] = [node("a", prompt="故事")]
    s.save_canvas(p["id"], canvas, 1)
    with pytest.raises(Conflict):
        s.save_canvas(p["id"], canvas, 1)
    assert Store(tmp_path).canvas(p["id"])["nodes"][0]["data"]["config"]["prompt"] == "故事"
    a = s.add_asset(p["id"], png(), "a.png")
    b = s.add_asset(p["id"], png(), "b.png")
    assert a["sha256"] == b["sha256"]
    assert not __import__("pathlib").Path(a["path"]).is_absolute()
    assert s.asset_path(a["id"]).read_bytes() == png()
    s.delete_asset(a["id"])
    with pytest.raises(ValueError):
        s.asset_path(a["id"])


def test_worker_cache_cancel_recovery(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("队列")
    canvas = s.canvas(p["id"])
    canvas["nodes"] = [node("a", prompt="一个故事"), node("b", "image.generate", prompt="蓝色的夜晚")]
    canvas["edges"] = [edge("a", "b")]
    s.save_canvas(p["id"], canvas, 1)
    w = Worker(s, mock=True)
    r = w.submit(p["id"], ["b"], False)
    for _ in range(10):
        w.tick()
    state = s.run(r["id"])
    assert state["status"] == "completed"
    assert len(state["tasks"]) == 2
    r2 = w.submit(p["id"], ["b"], False)
    for _ in range(10):
        w.tick()
    assert all(t["reused"] for t in s.run(r2["id"])["tasks"])
    r3 = w.submit(p["id"], ["b"], True)
    for t in s.run(r3["id"])["tasks"]:
        s.cancel(t["id"])
    w.tick()
    assert s.run(r3["id"])["status"] == "cancelled"
    r4 = w.submit(p["id"], ["b"], True)
    task = s.claim("old-worker")
    assert task
    s.update_task(task["id"], status="running", external_id="remote-job", lease_until=0)
    s.recover()
    assert s.task(task["id"])["external_id"] == "remote-job"
    assert s.task(task["id"])["status"] == "queued"


def test_single_claim(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("领取")
    c = s.canvas(p["id"])
    c["nodes"] = [node("a", prompt="x")]
    s.save_canvas(p["id"], c, 1)
    Worker(s, mock=True).submit(p["id"], [], False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda i: s.claim(str(i)), range(2)))
    assert sum(c is not None for c in claims) == 1


def test_runninghub_transport():
    import httpx
    from app.providers import RunningHub, ProviderError
    seen = []
    def handle(req):
        body = json.loads(req.content)
        seen.append(body)
        if req.url.path.endswith("create"):
            return httpx.Response(200, json={"code": 0, "data": {"taskId": "cloud-1"}})
        return httpx.Response(200, json={"code": 0, "data": "RUNNING"})
    provider = RunningHub("fake-key", httpx.Client(transport=httpx.MockTransport(handle)))
    job = provider.submit("image.generate", {"prompt": "夜晚"}, {})
    assert job == "cloud-1"
    assert provider.poll(job) == "RUNNING"
    assert seen[0]["workflowId"] == "2054172555577184258"
    assert "workflowId\t" not in seen[0]
    bad = RunningHub("key", httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429))))
    with pytest.raises(ProviderError) as e:
        bad.poll("1")
    assert e.value.retryable


def test_export_rejects_unapproved_and_missing(tmp_path):
    from app.store import Store
    from app.exporter import validate_timeline
    s = Store(tmp_path)
    p = s.create_project("导出")
    assert validate_timeline(s, p["id"], {"clips": []})
    assert validate_timeline(s, p["id"], {"clips": [{"assetId": "missing", "approved": True, "durationMs": 5000}]})


def test_api_security_roundtrip(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    app = create_app(tmp_path, token="test-token", start_worker=False)
    with TestClient(app) as client:
        assert client.get("/api/v1/projects").status_code == 401
        h = {"Authorization": "Bearer test-token"}
        assert client.get("/api/v1/projects", headers={**h, "Origin": "https://evil.example"}).status_code == 403
        r = client.post("/api/v1/projects", json={"name": "试拍"}, headers=h)
        assert r.status_code == 201
        pid = r.json()["id"]
        c = client.get(f"/api/v1/canvases/{pid}", headers=h).json()
        c["nodes"] = [node("a", prompt="测试")]
        assert client.put(f"/api/v1/canvases/{pid}", json=c, headers={**h, "If-Match": "1"}).status_code == 200
        assert client.put(f"/api/v1/canvases/{pid}", json=c, headers={**h, "If-Match": "1"}).status_code == 409
        r = client.post("/api/v1/assets/import", headers=h, data={"projectId": pid}, files={"file": ("测试.png", png(), "image/png")})
        assert r.status_code == 201
        aid = r.json()["id"]
        assert client.get(f"/api/v1/assets/{aid}/content", headers=h).content == png()
        assert client.get(f"/api/v1/assets/{aid}/content").status_code == 401


def test_adopted_candidate_is_output_not_reference(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("采用历史版本")
    old = s.add_asset(p["id"], png(), "old.png", "image")
    c = s.canvas(p["id"])
    c["nodes"] = [node("image", "image.generate", prompt="不应再次生成", assetId=old["id"])]
    s.save_canvas(p["id"], c, 1)
    w = Worker(s, mock=True)
    r = w.submit(p["id"], [], False)
    w.tick()
    assert s.run(r["id"])["tasks"][0]["output"]["assets"] == [old["id"]]
    r = w.submit(p["id"], [], True)
    w.tick()
    assert s.run(r["id"])["tasks"][0]["output"]["assets"] != [old["id"]]


def test_cancel_during_generation_does_not_adopt(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("取消竞态")
    c = s.canvas(p["id"])
    c["nodes"] = [node("image", "image.generate", prompt="测试")]
    s.save_canvas(p["id"], c, 1)
    w = Worker(s, mock=True)
    r = w.submit(p["id"], [], False)
    original = w.provider.fetch
    def late(*args):
        s.cancel(s.run(r["id"])["tasks"][0]["id"])
        return original(*args)
    w.provider.fetch = late
    w.tick()
    t = s.run(r["id"])["tasks"][0]
    assert t["status"] == "cancelled"
    assert not t["output"]


def test_missing_reference_stops_before_submission(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("缺失引用")
    a = s.add_asset(p["id"], png(), "ref.png")
    c = s.canvas(p["id"])
    c["nodes"] = [node("image", "image.generate", prompt="测试", referenceIds=[a["id"]])]
    s.save_canvas(p["id"], c, 1)
    s.asset_path(a["id"]).unlink()
    with pytest.raises(ValueError, match="ASSET_MISSING"):
        Worker(s, mock=True).submit(p["id"], [], False)


def test_cross_project_asset_rejected(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p, other = s.create_project("本项目"), s.create_project("其他项目")
    a = s.add_asset(other["id"], png(), "ref.png")
    c = s.canvas(p["id"])
    c["nodes"] = [node("image", "image.generate", prompt="测试", referenceIds=[a["id"]])]
    s.save_canvas(p["id"], c, 1)
    with pytest.raises(ValueError, match="其他项目"):
        Worker(s, mock=True).submit(p["id"], [], False)


@pytest.mark.parametrize("nodes,edges", [([None], []), ([{"id": "a", "data": None}], []), ([node("a")], [None]), ([node("a")], [{"id": "e", "data": None}]), ("not-a-list", [])])
def test_malformed_graph_returns_errors(nodes, edges):
    from app.graph import validate_graph
    assert validate_graph(nodes, edges)["errors"]


def test_wrong_asset_modality_rejected(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("素材类型校验")
    a = s.add_asset(p["id"], png(), "image.png")
    c = s.canvas(p["id"])
    c["nodes"] = [node("a", "asset.video", assetId=a["id"])]
    s.save_canvas(p["id"], c, 1)
    with pytest.raises(ValueError, match="类型"):
        Worker(s, mock=True).submit(p["id"], [], False)


def test_uncertain_submission_never_auto_resubmits(tmp_path):
    from app.store import Store
    from app.worker import Worker
    from app.providers import ProviderError
    s = Store(tmp_path)
    p = s.create_project("提交中断")
    c = s.canvas(p["id"])
    c["nodes"] = [node("a", "image.generate", prompt="test")]
    s.save_canvas(p["id"], c, 1)
    w = Worker(s, mock=True)
    attempts = []
    def timeout(*args):
        attempts.append(1)
        raise ProviderError("PROVIDER_NETWORK", "模拟提交响应丢失", True)
    w.provider.submit = timeout
    r = w.submit(p["id"], [], False)
    for _ in range(3):
        w.tick()
    t = s.run(r["id"])["tasks"][0]
    assert t["status"] == "failed" and t["error_code"] == "SUBMIT_UNCERTAIN"
    assert len(attempts) == 1
    with pytest.raises(ValueError, match="核查"):
        w.retry(t["id"])


def test_recovery_without_remote_id_requires_review(tmp_path):
    from app.store import Store
    from app.worker import Worker
    s = Store(tmp_path)
    p = s.create_project("中断恢复")
    c = s.canvas(p["id"])
    c["nodes"] = [node("a", "image.generate", prompt="test")]
    s.save_canvas(p["id"], c, 1)
    Worker(s, mock=True).submit(p["id"], [], False)
    t = s.claim("crashed")
    s.update_task(t["id"], submitted=1, lease_until=0)
    s.recover()
    assert s.task(t["id"])["status"] == "failed"
    assert s.task(t["id"])["error_code"] == "SUBMIT_UNCERTAIN"
