"""本地 API 和静态工作台，同源会话通过一次性启动 token 协商。"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation
from contextlib import asynccontextmanager
import os
from pathlib import Path
import secrets
import shutil
import sys
import time
from urllib.parse import urlparse
import uuid

from fastapi import FastAPI, File, Form, Header, Request, UploadFile, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.exporter import binary, export_timeline, validate_timeline
from app.graph import DEFINITIONS, validate_graph, snapshot_hash
from app.providers import capabilities
from app.store import Conflict, Store
from app.worker import Worker
from app.credentials import Settings
from app.project_storage import ProjectStorage
from app import directory_picker
from app.generation_profiles import generation_options, validate_profiles
from app.costs import BudgetLedger, money
from app.comfy import ComfyUI
from app.portable import export_project, import_project, export_template, import_template
from app.timeline import normalize_timeline
from app.text_result import edited_result

REPO = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[3]


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class RunRequest(BaseModel):
    projectId: str
    nodeIds: list[str] = []
    force: bool = False


def create_app(root=None, token=None, start_worker=True, settings=None, default_root=None):
    session_token = token or os.getenv("CANVAS_SESSION_TOKEN") or secrets.token_urlsafe(32)
    application_settings = settings or Settings()
    storage = ProjectStorage(application_settings.root)
    storage_error = ''
    data_root = root or default_root or os.getenv("CANVAS_DATA_DIR") or REPO / "data"
    if root is None:
        try:
            data_root = storage.resolve(data_root)
        except ValueError as exc:
            storage_error = str(exc)
    store = Store(data_root)
    worker = Worker(store, settings=application_settings)
    exports = ThreadPoolExecutor(max_workers=1, thread_name_prefix="canvas-export")

    @asynccontextmanager
    async def lifespan(app):
        # 导出中断不会假称成功；保留原始时间线快照供用户重试。
        for p in store.projects():
            with store.db(p["id"]) as con:
                rows = con.execute("SELECT key,body FROM documents WHERE key LIKE 'export:%'").fetchall()
            import json
            for row in rows:
                job = json.loads(row["body"])
                if job["status"] in ("queued", "running"):
                    store.put_document(p["id"], row["key"], {**job, "status": "failed", "error": "导出因应用退出而中断，请重新导出"})
        if start_worker:
            worker.start()
        yield
        worker.close()
        exports.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="无限画布本地 API", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.store, app.state.worker = store, worker
    app.state.settings = application_settings

    def host_allowed(host):
        return host.split(":")[0] in ("127.0.0.1", "localhost", "testserver")

    def origin_allowed(origin, host):
        if not origin:
            return True
        configured = set(os.getenv("CANVAS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(","))
        return origin in configured or origin in {"http://" + host, "https://" + host}

    def authorized(headers, cookies):
        supplied = headers.get("authorization", "").removeprefix("Bearer ") or cookies.get("canvas_session", "")
        return secrets.compare_digest(supplied, session_token)

    def error(code, message, status=400, details=None):
        return JSONResponse({"code": code, "message": message, "details": details, "requestId": uuid.uuid4().hex, "retryable": False}, status_code=status)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        host = request.headers.get("host", "")
        if not host_allowed(host):
            return error("INVALID_HOST", "只允许本机访问", 403)
        if not origin_allowed(request.headers.get("origin"), host):
            return error("INVALID_ORIGIN", "禁止跨站访问本地服务", 403)
        if request.url.path.startswith("/api/") and not authorized(request.headers, request.cookies):
            return error("UNAUTHORIZED", "会话已失效，请使用启动器重新打开工作台", 401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        return error("CONFLICT", str(exc), 409)

    @app.exception_handler(ValueError)
    async def value_handler(request, exc):
        return error("INVALID_INPUT", str(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        return error("INVALID_INPUT", "请求字段不符合要求", 422, [{"loc": e["loc"], "message": e["msg"]} for e in exc.errors()])

    @app.get("/healthz")
    def health():
        try:
            ffmpeg = bool(binary("ffmpeg") and binary("ffprobe"))
        except ValueError:
            ffmpeg = False
        return {"version": "0.1.0", "ready": True, "worker": bool(worker.thread and worker.thread.is_alive()), "ffmpeg": ffmpeg}

    @app.post("/api/v1/session")
    def session():
        response = JSONResponse({"ready": True})
        response.set_cookie("canvas_session", session_token, httponly=True, samesite="strict", path="/api", max_age=86400)
        return response

    @app.get("/api/v1/projects")
    def projects():
        return store.projects()

    @app.post("/api/v1/projects", status_code=201)
    def create_project(body: ProjectRequest):
        return store.create_project(body.name)

    @app.get("/api/v1/projects/{pid}")
    def project(pid: str):
        return store.document(pid, "project")

    @app.post('/api/v1/projects/import', status_code=201)
    async def import_archive(file: UploadFile = File()):
        data = await file.read(512 * 1024 * 1024 + 1)
        if len(data) > 512 * 1024 * 1024:
            raise ValueError('项目包超过 512 MB API 上传限制')
        return await asyncio.to_thread(import_project, store, data)

    @app.get('/api/v1/projects/{pid}/archive')
    def archive(pid: str):
        return Response(export_project(store, pid), media_type='application/zip', headers={'Content-Disposition': 'attachment; filename="canvas-project.zip"'})

    @app.get('/api/v1/projects/{pid}/template')
    def template(pid: str):
        return export_template(store, pid)

    @app.post('/api/v1/projects/{pid}/template')
    def apply_template(pid: str, body: dict):
        return import_template(store, pid, body)

    @app.get('/api/v1/settings')
    def get_settings():
        return application_settings.public()

    @app.get('/api/v1/settings/storage')
    def get_storage():
        return {**storage.status(store.root, storage_error), 'directoryPickerAvailable': bool(directory_picker.executable())}

    @app.post('/api/v1/settings/storage/browse')
    def browse_storage(body: dict):
        return {'directory': directory_picker.pick_directory(body.get('directory', ''))}

    @app.put('/api/v1/settings/storage')
    def save_storage(body: dict):
        nonlocal storage_error
        storage.save(body.get('directory'))
        storage_error = ''
        return storage.status(store.root)

    @app.delete('/api/v1/settings/storage')
    def cancel_storage_change():
        nonlocal storage_error
        storage.save(str(store.root))
        storage_error = ''
        return storage.status(store.root)

    @app.get('/api/v1/generation-options')
    def get_generation_options():
        return generation_options(application_settings)

    @app.get('/api/v1/queues')
    def queues():
        return store.queue_summary(application_settings.load()['concurrency'])

    @app.put('/api/v1/settings')
    def save_settings(body: dict):
        try:
            return application_settings.save(body)
        except ValueError as exc:
            return error('INVALID_INPUT', str(exc), 422)

    @app.post('/api/v1/settings/workflows/validate')
    def validate_workflow_import(body: dict):
        try:
            validate_profiles({'cloudWorkflows': [body]})
            return body
        except ValueError as exc:
            return error('INVALID_INPUT', str(exc), 422)

    @app.put('/api/v1/settings/credentials/{name}')
    def set_credential(name: str, body: dict):
        application_settings.set_key(name, body.get('key'))
        return application_settings.public()

    @app.delete('/api/v1/settings/credentials/{name}')
    def delete_credential(name: str):
        application_settings.delete_key(name)
        return application_settings.public()

    @app.get('/api/v1/settings/diagnostics')
    def diagnostics():
        config = application_settings.load()
        disk = shutil.disk_usage(store.root)
        return {'comfyui': ComfyUI(config['comfyUrl'], config['comfyWorkflows']).diagnostics(),
                'ffmpeg': health()['ffmpeg'], 'diskFreeBytes': disk.free, 'diskTotalBytes': disk.total,
                'worker': bool(worker.thread and worker.thread.is_alive()), 'concurrency': config['concurrency']}

    @app.get('/api/v1/projects/{pid}/costs')
    def costs(pid: str):
        return BudgetLedger(store).summary(pid)

    @app.put("/api/v1/projects/{pid}/settings")
    def project_settings(pid: str, body: dict):
        project = store.document(pid, "project")
        if not body.keys() <= {'cloudEnabled', 'budget'}:
            return error('INVALID_INPUT', '项目设置包含未知字段', 422)
        if 'cloudEnabled' in body and type(body['cloudEnabled']) is not bool:
            return error('INVALID_INPUT', 'cloudEnabled 必须是布尔值', 422)
        if body.get('budget') is not None and 'budget' in body:
            try:
                budget = body['budget']
                value = Decimal(str(budget['limit']))
                if not value.is_finite() or value < 0 or budget.get('currency') not in ('CNY', 'USD'):
                    return error('INVALID_INPUT', '预算或币种无效', 422)
                body['budget'] = {'limit': money(value), 'currency': budget['currency']}
            except (KeyError, TypeError, InvalidOperation):
                return error('INVALID_INPUT', '预算参数无效', 422)
        project['settings'].update(body)
        return store.put_document(pid, "project", project)

    @app.post("/api/v1/projects/{pid}/backup")
    def backup(pid: str):
        target = store.backup(pid)
        return {"name": target.name, "message": "已保存数据库快照；媒体源文件保留在项目 assets 目录"}

    @app.get("/api/v1/canvases/{pid}")
    def canvas(pid: str):
        return store.canvas(pid)

    @app.put("/api/v1/canvases/{pid}")
    def save_canvas(pid: str, body: dict, if_match: str = Header()):
        if not isinstance(body.get("nodes"), list) or not isinstance(body.get("edges"), list):
            raise ValueError("画布需包含节点和连线数组")
        if len(body["nodes"]) > 2000 or len(body["edges"]) > 5000:
            raise ValueError("画布超过当前节点或连线数量上限")
        result = validate_graph(body["nodes"], body["edges"])
        if result["errors"]:
            raise ValueError("；".join(result["errors"]))
        return store.save_canvas(pid, body, int(if_match.strip('"')))

    @app.get("/api/v1/definitions")
    def definitions():
        return DEFINITIONS

    @app.post("/api/v1/workflows/validate")
    def validate(body: dict):
        return validate_graph(body.get("nodes", []), body.get("edges", []))

    @app.get("/api/v1/projects/{pid}/assets")
    def assets(pid: str):
        return store.assets(pid)

    @app.post("/api/v1/assets/import", status_code=201)
    async def import_asset(projectId: str = Form(), file: UploadFile = File()):
        data = await file.read(512 * 1024 * 1024 + 1)
        return await asyncio.to_thread(store.add_asset, projectId, data, file.filename or "input.bin")

    @app.get("/api/v1/assets/{aid}/content")
    def content(aid: str, download: bool = False):
        asset = store.asset(aid)
        return FileResponse(store.asset_path(aid), media_type=asset["mime"], filename=asset['name'] if download else None)

    @app.get("/api/v1/assets/{aid}/thumbnail")
    def thumbnail(aid: str):
        import io
        from PIL import Image, ImageOps
        from fastapi.responses import Response
        asset = store.asset(aid)
        if asset["mime"].startswith("video/"):
            from app.video_thumbnail import video_thumbnail
            return Response(video_thumbnail(store.asset_path(aid)), media_type="image/jpeg",
                            headers={"Cache-Control": "private, max-age=3600"})
        if not asset["mime"].startswith("image/"):
            raise ValueError("此素材无图片缩略图")
        with Image.open(store.asset_path(aid)) as source:
            with ImageOps.exif_transpose(source) as image:
                image.thumbnail((480, 480))
                with image.convert("RGBA") as foreground, Image.new("RGB", image.size, "white") as preview:
                    preview.paste(foreground, mask=foreground.getchannel("A"))
                    out = io.BytesIO()
                    preview.save(out, "JPEG", quality=80)
        return Response(out.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})

    @app.delete("/api/v1/assets/{aid}")
    def delete_asset(aid: str):
        store.delete_asset(aid)
        return {"deleted": True}

    @app.patch('/api/v1/assets/{aid}')
    def rename_asset(aid: str, body: dict):
        return store.rename_asset(aid, body.get('name'))

    @app.post("/api/v1/runs", status_code=202)
    def run(body: RunRequest):
        return worker.submit(body.projectId, body.nodeIds, body.force)

    @app.post('/api/v1/runs/estimate')
    def estimate(body: RunRequest):
        return worker.submit(body.projectId, body.nodeIds, body.force, dry_run=True)

    @app.get("/api/v1/runs/{rid}")
    def run_status(rid: str):
        return store.run(rid)

    @app.get("/api/v1/projects/{pid}/tasks")
    def tasks(pid: str):
        return store.tasks(pid)

    @app.post("/api/v1/tasks/{tid}/cancel")
    def cancel(tid: str):
        return store.cancel(tid)

    @app.post('/api/v1/tasks/{tid}/text-preview')
    def preview_text(tid: str, body: dict):
        task = store.task(tid)
        if task['status'] != 'completed' or not isinstance(task['output'].get('text'), str):
            raise ValueError('只能编辑已完成的文本结果')
        return edited_result(task['snapshot']['kind'], body.get('text'), task['output'])

    @app.post("/api/v1/tasks/{tid}/retry")
    def retry(tid: str, body: dict):
        return worker.retry(tid, bool(body.get("confirmUncertain")))

    @app.get("/api/v1/providers")
    def providers():
        return capabilities(application_settings)

    @app.get("/api/v1/projects/{pid}/timeline")
    def timeline(pid: str):
        return store.document(pid, "timeline")

    @app.put("/api/v1/projects/{pid}/timeline")
    def save_timeline(pid: str, body: dict):
        normalized = normalize_timeline(body, allow_empty=True)
        return store.put_document(pid, "timeline", normalized, body.get("version"))

    @app.get("/api/v1/projects/{pid}/people")
    def people(pid: str):
        return store.document(pid, "people")

    @app.put("/api/v1/projects/{pid}/people")
    def save_people(pid: str, body: dict):
        return store.put_document(pid, "people", body, body.get("version"))

    def execute_export(pid, job):
        key = "export:" + job["id"]
        store.put_document(pid, key, {**job, "status": "running"})
        try:
            output = export_timeline(store, pid, job["timeline"], job["id"], preview=job.get('preview', False))
            store.put_document(pid, key, {**job, "status": "completed", "output": output})
        except Exception as exc:
            store.put_document(pid, key, {**job, "status": "failed", "error": str(exc)})

    @app.post("/api/v1/exports", status_code=202)
    def export(body: dict):
        pid = body.get("projectId", "")
        timeline = store.document(pid, "timeline")
        errors = validate_timeline(store, pid, timeline)
        if errors:
            raise ValueError("；".join(errors))
        binary("ffmpeg")
        binary("ffprobe")
        preview = body.get('preview', False)
        if type(preview) is not bool:
            raise ValueError('预览标志必须是布尔值')
        input_hash = snapshot_hash({k: v for k, v in normalize_timeline(timeline).items() if k != 'version'})
        if preview:
            # 不复用旧的低分辨率预览或原尺寸居中、带黑框的旧布局。
            input_hash = snapshot_hash({'timelineHash': input_hash, 'previewRenderer': 'full-resolution-resize-v2'})
            import json
            with store.db(pid) as con:
                candidates = [json.loads(row[0]) for row in con.execute("SELECT body FROM documents WHERE key LIKE 'export:%'")]
            for candidate in reversed(candidates):
                if candidate.get('preview') and candidate.get('inputHash') == input_hash and candidate['status'] in ('queued', 'running', 'completed'):
                    if candidate['status'] != 'completed' or (store.project_dir(pid) / candidate['output']['path']).is_file():
                        return candidate
        job = {"id": pid + "_" + uuid.uuid4().hex, "projectId": pid, "status": "queued", "timeline": timeline,
               "createdAt": time.time(), 'preview': preview, 'inputHash': input_hash}
        store.put_document(pid, "export:" + job["id"], job)
        exports.submit(execute_export, pid, job)
        return job

    @app.post('/api/v1/projects/{pid}/preview', status_code=202)
    def composed_preview(pid: str):
        return export({'projectId': pid, 'preview': True})

    @app.get("/api/v1/exports/{eid}")
    def export_status(eid: str):
        return store.document(eid, "export:" + eid)

    @app.get("/api/v1/exports/{eid}/content")
    def export_content(eid: str):
        job = store.document(eid, "export:" + eid)
        if job["status"] != "completed":
            raise ValueError("导出尚未完成")
        directory = store.project_dir(eid)
        path = (directory / job["output"]["path"]).resolve()
        if not path.is_relative_to(directory / "exports"):
            raise ValueError("导出路径无效")
        return FileResponse(path, media_type="video/mp4", filename="短剧成片.mp4")

    @app.get("/api/v1/events")
    def events(projectId: str, lastEventId: int = 0):
        return store.events(projectId, lastEventId)

    @app.websocket("/api/v1/events/ws")
    async def websocket(ws: WebSocket, projectId: str, lastEventId: int = 0):
        host = ws.headers.get("host", "")
        if not host_allowed(host) or not origin_allowed(ws.headers.get("origin"), host) or not authorized(ws.headers, ws.cookies):
            await ws.close(code=1008)
            return
        await ws.accept()
        cursor = lastEventId
        try:
            while True:
                rows = await asyncio.to_thread(store.events, projectId, cursor)
                for row in rows:
                    await ws.send_json(row)
                    cursor = row["eventId"]
                await asyncio.sleep(1)
        except Exception:
            return

    dist = REPO / "apps" / "desktop" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="studio")
    return app


app = create_app()
