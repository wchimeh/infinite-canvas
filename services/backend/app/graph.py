"""不依赖 UI/Provider 的图契约。sequence 边不参与执行。"""
import hashlib
import json
import math


def definition(name, inputs, outputs):
    return {"displayName": name, "inputs": inputs, "outputs": outputs, "version": 1}


DEFINITIONS = {
    "story.prompt": definition("故事 / 文本", {}, {"text": "text"}),
    "text.concat": definition("文本拼接", {"text" + (str(i) if i > 1 else ""): "text" for i in range(1, 11)}, {"text": "text"}),
    "script.expand": definition("剧本扩写", {"text": "text"}, {"text": "text"}),
    "shots.extract": definition("提取分镜", {"text": "text"}, {"text": "text"}),
    "shots.select": definition("分镜选择", {"text": "text"}, {"text": "text"}),
    "prompt.video_expand": definition("视频提示词扩写", {"text": "text", **{port + (str(i) if i > 1 else ""): port for port, count in [('image', 9), ('audio', 3), ('video', 3)] for i in range(1, count + 1)}}, {"text": "text"}),
    "character.extract": definition("提取角色", {"text": "text"}, {"text": "text"}),
    "image.character": definition("生成角色图", {"text": "text", **{"image" + (str(i) if i > 1 else ""): "image" for i in range(1, 9)}}, {"image": "image"}),
    "location.extract": definition("提取场景", {"text": "text"}, {"text": "text"}),
    "image.location": definition("生成场景图", {"text": "text", **{"image" + (str(i) if i > 1 else ""): "image" for i in range(1, 9)}}, {"image": "image"}),
    "image.prop": definition("生成道具图", {"text": "text", **{"image" + (str(i) if i > 1 else ""): "image" for i in range(1, 9)}}, {"image": "image"}),
    "character.reference": definition("角色参考", {}, {"image": "image"}),
    "location.reference": definition("场景参考", {}, {"image": "image"}),
    "asset.image": definition("图片素材", {}, {"image": "image"}),
    "asset.video": definition("视频素材", {}, {"video": "video"}),
    "asset.audio": definition("音频素材", {}, {"audio": "audio"}),
    "audio.extract": definition("提取视频音频", {"video": "video"}, {"audio": "audio"}),
    "frame.extract": definition("提取视频帧", {"video": "video"}, {"image": "image"}),
    "audio.trim": definition("音频裁剪", {"audio": "audio"}, {"audio": "audio"}),
    "video.trim": definition("视频裁剪", {"video": "video"}, {"video": "video"}),
    "image.generate": definition("生成分镜图", {"text": "text", **{"image" + (str(i) if i > 1 else ""): "image" for i in range(1, 9)}}, {"image": "image"}),
    "image.variation": definition("参考图创作", {"text": "text", **{"image" + (str(i) if i > 1 else ""): "image" for i in range(1, 9)}}, {"image": "image"}),
    "video.image_to_video": definition("生成视频", {"text": "text", **{port + (str(i) if i > 1 else ''): port for port, limit in [('image', 9), ('video', 3), ('audio', 3)] for i in range(1, limit + 1)}, **{'videoAudio' + (str(i) if i > 1 else ''): 'audio' for i in range(1, 4)}}, {"video": "video"}),
    "audio.tts": definition("对白 / 配音", {"text": "text", "audio": "audio"}, {"audio": "audio"}),
    "video.combat": definition("生成视频-武打", {"text": "text", **{port + (str(i) if i > 1 else ''): port for port, limit in [('image', 9), ('audio', 3), ('video', 3)] for i in range(1, limit + 1)}}, {"video": "video"}),
    "video.sound_effects": definition("视频音效", {"text": "text", "video": "video"}, {"video": "video"}),
}


def node_kind(n):
    return n.get("data", {}).get("kind", "")


def snapshot_hash(snapshot):
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_graph(nodes, edges):
    errors = []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {"errors": ["节点和连接必须是数组"], "warnings": []}
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get('id'), str) or not isinstance(n.get('data'), dict):
            errors.append("节点必须包含字符串 ID 和 data 对象")
            continue
        data = n['data']
        if not isinstance(data.get('kind'), str) or not isinstance(data.get('config', {}), dict):
            errors.append("节点类型或参数结构无效")
            continue
        config = data.get('config', {})
        if data.get('kind') == 'text.concat' and not isinstance(config.get('separator', '\n'), str):
            errors.append("文本拼接分隔符必须是字符串")
        if not isinstance(config.get('prompt', ''), str) or not isinstance(config.get('referenceIds', []), list) or not all(isinstance(i, str) for i in config.get('referenceIds', [])):
            errors.append("提示词必须是文本，参考素材必须是 ID 数组")
        pos = n.get('position', {})
        if not isinstance(pos, dict) or any(not isinstance(pos.get(k), (float, int)) or not math.isfinite(pos[k]) for k in ('x', 'y')):
            errors.append("节点坐标无效")
    for e in edges:
        if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ('id', 'source', 'target', 'sourceHandle', 'targetHandle')) or not isinstance(e.get('data', {}), dict):
            errors.append("连接必须包含 ID、源/目标节点和端口")
    if errors:
        return {"errors": errors, "warnings": []}
    ids = [n.get("id") for n in nodes]
    if len(set(ids)) != len(ids) or any(not isinstance(i, str) or not i for i in ids):
        errors.append("节点 ID 缺失或重复")
    by_id = {n.get("id"): n for n in nodes}
    for n in nodes:
        if node_kind(n) not in DEFINITIONS:
            errors.append(f"未知节点类型：{node_kind(n)}")
    occupied = set()
    edge_ids = set()
    for e in edges:
        if e.get("id") in edge_ids:
            errors.append("连接 ID 重复")
        edge_ids.add(e.get("id"))
        source, target = by_id.get(e.get("source")), by_id.get(e.get("target"))
        if source is None or target is None:
            errors.append("连接引用了不存在的节点")
            continue
        kind = e.get("data", {}).get("kind", "data")
        if kind == "sequence":
            continue
        if kind not in ("data", "reference"):
            errors.append("未知连接种类")
        out = DEFINITIONS.get(node_kind(source), {}).get("outputs", {}).get(e.get("sourceHandle"))
        inp = DEFINITIONS.get(node_kind(target), {}).get("inputs", {}).get(e.get("targetHandle"))
        if not out or not inp or inp != out:
            errors.append(f"端口类型不兼容：{e.get('source')} → {e.get('target')}")
        port = (e.get("target"), e.get("targetHandle"))
        if inp == "text" and port in occupied:
            errors.append("文本输入只允许一条连接")
        occupied.add(port)
    if not errors:
        try:
            execution_order(nodes, edges)
        except ValueError as exc:
            errors.append(str(exc))
    return {"errors": errors, "warnings": []}


def execution_order(nodes, edges, selected=None):
    ids = [n["id"] for n in nodes]
    parents = {i: [] for i in ids}
    for e in edges:
        if e.get("data", {}).get("kind") != "sequence":
            if e["target"] not in parents or e["source"] not in parents:
                raise ValueError("连接引用了不存在的节点")
            parents[e["target"]].append(e["source"])
    result, active, visited = [], set(), set()

    for root in selected or ids:
        stack = [(root, False)]
        while stack:
            i, exiting = stack.pop()
            if i not in parents:
                raise ValueError("选中节点不存在")
            if exiting:
                active.remove(i)
                visited.add(i)
                result.append(i)
                continue
            if i in visited:
                continue
            if i in active:
                raise ValueError("存在循环依赖")
            active.add(i)
            stack.append((i, True))
            stack.extend((parent, False) for parent in reversed(parents[i]))
    return result
