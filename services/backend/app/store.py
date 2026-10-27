"""每项目 SQLite/WAL；不可变内容文件；带租约的事务任务队列。"""
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager, closing

from PIL import Image


class Conflict(ValueError):
    pass


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS documents (key TEXT PRIMARY KEY, body TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, body TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL, node_id TEXT NOT NULL, status TEXT NOT NULL,
 snapshot TEXT NOT NULL, deps TEXT NOT NULL, output TEXT NOT NULL DEFAULT '{}',
 external_id TEXT, input_hash TEXT, error TEXT, error_code TEXT,
 retryable INTEGER NOT NULL DEFAULT 0, reused INTEGER NOT NULL DEFAULT 0,
 attempt INTEGER NOT NULL DEFAULT 0, lease_until REAL NOT NULL DEFAULT 0,
 owner TEXT, next_poll REAL NOT NULL DEFAULT 0, submitted INTEGER NOT NULL DEFAULT 0,
 created_at REAL NOT NULL, updated_at REAL NOT NULL, deadline_at REAL
);
CREATE INDEX IF NOT EXISTS task_status ON tasks(status, next_poll);
CREATE INDEX IF NOT EXISTS task_cache ON tasks(input_hash, status);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT NOT NULL);
PRAGMA user_version=2;
"""


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, id):
        pid = str(id).split("_")[0]
        if not re.fullmatch(r"[a-f0-9]{32}", pid):
            raise ValueError("无效的项目或资源 ID")
        return self.root / pid

    @contextmanager
    def db(self, id):
        path = self.project_dir(id) / "project.db"
        if not path.is_file():
            raise ValueError("项目不存在")
        con = sqlite3.connect(path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            if con.execute("PRAGMA user_version").fetchone()[0] < 2:
                con.execute("BEGIN IMMEDIATE")
                # 持有写锁后复查，避免多个调度连接重复迁移。
                if con.execute("PRAGMA user_version").fetchone()[0] < 2:
                    con.execute("ALTER TABLE tasks ADD COLUMN deadline_at REAL")
                    con.execute("PRAGMA user_version=2")
                con.commit()
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def create_project(self, name):
        name = str(name).strip()
        if not name or len(name) > 100:
            raise ValueError("项目名称需要 1–100 个字符")
        pid = uuid.uuid4().hex
        directory = self.project_dir(pid)
        directory.mkdir()
        for name_ in ("assets", "exports", "backups"):
            (directory / name_).mkdir()
        with sqlite3.connect(directory / "project.db") as con:
            con.executescript(SCHEMA)
        project = {"id": pid, "name": name, "createdAt": time.time(), "settings": {"cloudEnabled": False}}
        self.put_document(pid, "project", project)
        self.put_document(pid, "canvas", {"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}})
        self.put_document(pid, "timeline", {"clips": [], "audio": [], "subtitles": [], "fps": 30, "width": 1080, "height": 1920})
        self.put_document(pid, "people", {"characters": [], "locations": [], "shots": []})
        return project

    def projects(self):
        result = []
        for directory in self.root.iterdir():
            if re.fullmatch(r"[a-f0-9]{32}", directory.name) and (directory / "project.db").is_file():
                result.append(self.document(directory.name, "project"))
        return sorted(result, key=lambda p: p["createdAt"], reverse=True)

    def document(self, pid, key):
        with self.db(pid) as con:
            r = con.execute("SELECT * FROM documents WHERE key=?", (key,)).fetchone()
        if r is None:
            raise ValueError("记录不存在")
        return {**json.loads(r["body"]), "version": r["version"]}

    def put_document(self, pid, key, body, version=None):
        clean = {k: v for k, v in body.items() if k != "version"}
        with self.db(pid) as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT version FROM documents WHERE key=?", (key,)).fetchone()
            if version is not None and (not row or row[0] != version):
                raise Conflict("项目已在其他窗口修改，请重新打开后再保存")
            new_version = row[0] + 1 if row else 1
            con.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?)", (key, encode(clean), new_version))
        return {**clean, "version": new_version}

    def canvas(self, pid):
        return self.document(pid, "canvas")

    def save_canvas(self, pid, body, version):
        return self.put_document(pid, "canvas", body, version)

    def asset(self, aid):
        with self.db(aid) as con:
            row = con.execute("SELECT body FROM assets WHERE id=? AND deleted=0", (aid,)).fetchone()
        if row is None:
            raise ValueError("素材不存在或已移除")
        return json.loads(row[0])

    def assets(self, pid):
        with self.db(pid) as con:
            return [json.loads(r[0]) for r in con.execute("SELECT body FROM assets WHERE deleted=0 ORDER BY rowid DESC")]

    def rename_asset(self, aid, name):
        if not isinstance(name, str):
            raise ValueError('素材名称必须为文本')
        name = name.strip()
        if not name or len(name) > 200:
            raise ValueError('素材名称须为 1–200 个字符')
        if any(ord(char) < 32 or ord(char) == 127 or char in '\\/:*?"<>|' for char in name):
            raise ValueError('素材名称不能包含换行或 \\ / : * ? " < > | 等字符')
        with self.db(aid) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT body FROM assets WHERE id=? AND deleted=0', (aid,)).fetchone()
            if row is None:
                raise ValueError('素材不存在或已移除')
            asset = json.loads(row[0])
            asset['name'] = name
            con.execute('UPDATE assets SET body=? WHERE id=? AND deleted=0', (encode(asset), aid))
        return asset

    def add_asset(self, pid, data, filename, node_id=None, run_id=None):
        self.document(pid, "project")
        if not data or len(data) > 512 * 1024 * 1024:
            raise ValueError("文件为空或超过 512 MB")
        ext = Path(filename).suffix.lower()
        allowed = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".mov", ".wav", ".mp3", ".m4a", ".ogg", ".flac"}
        if ext not in allowed:
            raise ValueError("仅支持图片、视频和音频素材")
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        width = height = None
        if mime.startswith("image/"):
            try:
                with Image.open(io.BytesIO(data)) as im:
                    width, height = im.size
                    im.verify()
            except Exception as exc:
                raise ValueError("图片内容损坏或格式不支持") from exc
        sha = hashlib.sha256(data).hexdigest()
        relative = f"assets/{sha[:2]}/{sha}{ext}"
        target = self.project_dir(pid) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        is_new = not target.exists()
        if is_new:
            temp = target.with_suffix("." + uuid.uuid4().hex + ".partial")
            try:
                with temp.open("xb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                if hashlib.sha256(temp.read_bytes()).hexdigest() != sha:
                    raise ValueError("素材校验失败")
                os.replace(temp, target)
            finally:
                temp.unlink(missing_ok=True)
        aid = pid + "_" + uuid.uuid4().hex
        display_name = Path(filename).name
        if node_id and mime.startswith('image/'):
            node = next((n for n in self.canvas(pid).get('nodes', []) if n['id'] == node_id), None)
            if node:
                node_data = node.get('data', {})
                config = node_data.get('config', {})
                group, key = {'image.character': ('characters', 'characterId'),
                              'image.location': ('locations', 'locationId')}.get(node_data.get('kind'), (None, None))
                subject = next((item for item in self.document(pid, 'people').get(group, [])
                                if item['id'] == config.get(key)), None) if group else None
                prefix = (subject or {}).get('name') or node_data.get('title') or ''
                prefix = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', prefix).strip(' .')[:100]
                if prefix:
                    display_name = f'{prefix}_{display_name}'
        asset = {"id": aid, "revisionId": aid, "projectId": pid, "name": display_name,
                 "sha256": sha, "path": relative, "mime": mime, "size": len(data), "width": width, "height": height,
                 "nodeId": node_id, "runId": run_id, "createdAt": time.time()}
        try:
            with self.db(pid) as con:
                con.execute("INSERT INTO assets(id,body) VALUES (?,?)", (aid, encode(asset)))
                self.event(con, {"event": "asset.created", "assetId": aid, "projectId": pid, "nodeId": node_id})
        except Exception:
            # 文件可能被并发导入引用；只清理没有任何记录引用的对象。
            with self.db(pid) as con:
                used = any(json.loads(r[0])["path"] == relative for r in con.execute("SELECT body FROM assets"))
            if is_new and not used:
                target.unlink(missing_ok=True)
            raise
        return asset

    def asset_path(self, aid):
        a = self.asset(aid)
        directory = self.project_dir(aid)
        path = (directory / a["path"]).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError("ASSET_MISSING：素材源文件缺失")
        return path

    def delete_asset(self, aid):
        self.asset(aid)
        with self.db(aid) as con:
            con.execute("UPDATE assets SET deleted=1 WHERE id=?", (aid,))

    @staticmethod
    def event(con, body):
        con.execute("INSERT INTO events(body) VALUES (?)", (encode({**body, "timestamp": time.time()}),))

    def events(self, pid, after=0):
        with self.db(pid) as con:
            return [{**json.loads(r["body"]), "eventId": r["id"]} for r in con.execute(
                "SELECT * FROM events WHERE id>? ORDER BY id LIMIT 500", (after,))]

    def create_run(self, pid, specs, force=False):
        rid = pid + "_" + uuid.uuid4().hex
        run = {"id": rid, "projectId": pid, "force": force, "createdAt": time.time()}
        tids = {s["nodeId"]: pid + "_" + uuid.uuid4().hex for s in specs}
        with self.db(pid) as con:
            con.execute("BEGIN IMMEDIATE")
            # 同一节点不能同时有两个未终结运行。
            for spec in specs:
                if con.execute("SELECT 1 FROM tasks WHERE node_id=? AND status IN ('queued','running','cancel_requested')", (spec["nodeId"],)).fetchone():
                    raise Conflict("选中节点已有未完成任务")
            con.execute("INSERT INTO runs VALUES (?,?)", (rid, encode(run)))
            for spec in specs:
                con.execute("INSERT INTO tasks(id,run_id,node_id,status,snapshot,deps,created_at,updated_at) VALUES (?,?,?,'queued',?,?,?,?)",
                            (tids[spec["nodeId"]], rid, spec["nodeId"], encode(spec["snapshot"]),
                             encode([tids[d] for d in spec["deps"]]), time.time(), time.time()))
                if 'cachedOutput' in spec:
                    con.execute("UPDATE tasks SET status='completed',reused=1,output=?,input_hash=? WHERE id=?",
                                (encode(spec['cachedOutput']), spec['cachedHash'], tids[spec['nodeId']]))
        return {**run, "status": "queued", "runId": rid}

    @staticmethod
    def task_row(r):
        if r is None:
            raise ValueError("任务不存在")
        d = dict(r)
        for key in ("snapshot", "deps", "output"):
            d[key] = json.loads(d[key])
        return d

    def task(self, tid):
        with self.db(tid) as con:
            return self.task_row(con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone())

    def tasks(self, pid):
        with self.db(pid) as con:
            return [self.task_row(r) for r in con.execute("""
                SELECT * FROM tasks
                WHERE status IN ('queued', 'running', 'cancel_requested')
                   OR id IN (SELECT id FROM tasks ORDER BY created_at DESC, id DESC LIMIT 200)
                ORDER BY created_at DESC, id DESC
            """)]

    def run(self, rid):
        with self.db(rid) as con:
            r = con.execute("SELECT body FROM runs WHERE id=?", (rid,)).fetchone()
            if not r:
                raise ValueError("运行不存在")
            run = json.loads(r[0])
            tasks = [self.task_row(t) for t in con.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY created_at", (rid,))]
        statuses = {t["status"] for t in tasks}
        status = "running" if statuses & {"queued", "running", "cancel_requested"} else "failed" if statuses & {"failed", "blocked"} else "cancelled" if "cancelled" in statuses else "completed"
        return {**run, "status": status, "tasks": tasks}

    def update_task(self, tid, expected=None, **fields):
        allowed = {"status", "output", "external_id", "input_hash", "error", "error_code", "retryable", "reused", "attempt", "lease_until", "owner", "next_poll", "submitted", "deadline_at"}
        if not fields.keys() <= allowed:
            raise ValueError("未知任务字段")
        fields["updated_at"] = time.time()
        if "output" in fields:
            fields["output"] = encode(fields["output"])
        with self.db(tid) as con:
            assignments = ",".join(f"{k}=?" for k in fields)
            args = [*fields.values(), tid]
            where = "id=?"
            if expected:
                where += " AND status=?"
                args.append(expected)
            changed = con.execute(f"UPDATE tasks SET {assignments} WHERE {where}", args).rowcount
            if changed:
                row = con.execute('SELECT run_id,node_id,status FROM tasks WHERE id=?', (tid,)).fetchone()
                self.event(con, {"event": "task.updated", "taskId": tid, "status": row['status'],
                                 "projectId": tid.split('_')[0], "runId": row['run_id'], "nodeId": row['node_id']})
        return bool(changed)

    @staticmethod
    def modality(snapshot):
        kind = snapshot['kind']
        if kind in ('story.prompt', 'shots.select', 'text.concat', 'frame.extract', 'audio.extract', 'audio.trim', 'video.trim') or kind.startswith('asset.') or kind.endswith('.reference') or snapshot.get('adopted'):
            return 'local'
        return 'video' if kind.startswith('video.') else 'audio' if kind.startswith('audio.') else 'image' if kind.startswith('image.') else 'text'

    @classmethod
    def queue_name(cls, snapshot):
        modality = cls.modality(snapshot)
        return 'media' if modality in ('image', 'video') else modality

    def queue_summary(self, capacities):
        queues = {name: {'id': name, 'capacity': capacities.get(name, 1), 'occupied': 0, 'waiting': 0}
                  for name in ('text', 'media', 'audio')}
        for project in self.projects():
            with self.db(project['id']) as con:
                for row in con.execute("SELECT snapshot,status,external_id FROM tasks WHERE status IN ('queued','running','cancel_requested')"):
                    queue = self.queue_name(json.loads(row['snapshot']))
                    if queue not in queues:
                        continue
                    field = 'waiting' if row['status'] == 'queued' and not row['external_id'] else 'occupied'
                    queues[queue][field] += 1
        return {'queues': list(queues.values())}

    def claim(self, owner, capacities=None, queue=None):
        # 单独的 SQLite gate 跨项目、跨进程序列化容量检查与领取。
        # 项目数据库仍各自独立，可单独迁移；gate 不保存项目事实。
        with closing(sqlite3.connect(self.root / 'queue-gate.db', timeout=15)) as gate:
            gate.execute('BEGIN IMMEDIATE')
            try:
                return self._claim(owner, capacities, queue)
            finally:
                gate.commit()

    def _claim(self, owner, capacities, queue=None):
        occupied = {}
        character_busy = False
        for project in self.projects():
            with self.db(project['id']) as con:
                for row in con.execute("SELECT snapshot FROM tasks WHERE status IN ('running','cancel_requested') OR (status='queued' AND external_id IS NOT NULL)"):
                    snapshot = json.loads(row[0])
                    if snapshot['kind'] == 'image.character' and not snapshot.get('adopted'):
                        character_busy = True
                    if capacities is not None:
                        modality = self.queue_name(snapshot) if 'media' in capacities else self.modality(snapshot)
                        occupied[modality] = occupied.get(modality, 0) + 1
        for project in self.projects():
            with self.db(project["id"]) as con:
                con.execute("BEGIN IMMEDIATE")
                for row in con.execute("SELECT * FROM tasks WHERE status='queued' AND next_poll<=? ORDER BY created_at", (time.time(),)).fetchall():
                    task = self.task_row(row)
                    if queue is not None and self.queue_name(task['snapshot']) != queue:
                        continue
                    if character_busy and task['snapshot']['kind'] == 'image.character' and not task['snapshot'].get('adopted') and not task['external_id']:
                        continue
                    modality = self.queue_name(task['snapshot']) if capacities is not None and 'media' in capacities else self.modality(task['snapshot'])
                    if capacities is not None and not task['external_id'] and occupied.get(modality, 0) >= capacities.get(modality, 8 if modality == 'local' else 1):
                        continue
                    deps = [con.execute("SELECT status FROM tasks WHERE id=?", (d,)).fetchone()[0] for d in task["deps"]]
                    if any(d in ("failed", "blocked", "cancelled") for d in deps):
                        con.execute("UPDATE tasks SET status='blocked', error='上游任务未成功' WHERE id=?", (task["id"],))
                        self.event(con, {'event': 'task.updated', 'projectId': project['id'], 'runId': task['run_id'], 'nodeId': task['node_id'], 'taskId': task['id'], 'status': 'blocked'})
                        continue
                    if any(d != "completed" for d in deps):
                        continue
                    con.execute("UPDATE tasks SET status='running', owner=?,lease_until=?,updated_at=? WHERE id=?", (owner, time.time() + 180, time.time(), task["id"]))
                    self.event(con, {'event': 'task.updated', 'projectId': project['id'], 'runId': task['run_id'], 'nodeId': task['node_id'], 'taskId': task['id'], 'status': 'running'})
                    return {**task, "status": "running", "owner": owner}
        return None

    def recover(self):
        for p in self.projects():
            with self.db(p["id"]) as con:
                con.execute("UPDATE tasks SET status='failed',error_code='SUBMIT_UNCERTAIN',error='云端提交结果不确定，请核查账单后重试',retryable=0 WHERE status='running' AND lease_until<? AND submitted=1 AND external_id IS NULL", (time.time(),))
                con.execute("UPDATE tasks SET status='queued',owner=NULL WHERE status='running' AND lease_until<?", (time.time(),))
                con.execute("UPDATE tasks SET status='cancelled' WHERE status='cancel_requested' AND lease_until<?", (time.time(),))

    def cancel(self, tid):
        t = self.task(tid)
        if t["status"] in ("queued", "running"):
            self.update_task(tid, expected=t["status"], status="cancel_requested" if t["status"] == "running" else "cancelled")
        return self.task(tid)

    def cached(self, pid, input_hash):
        with self.db(pid) as con:
            r = con.execute("SELECT output FROM tasks WHERE status='completed' AND input_hash=? ORDER BY updated_at DESC LIMIT 1", (input_hash,)).fetchone()
        if not r:
            return None
        output = json.loads(r[0])
        try:
            for aid in output.get("assets", []):
                self.asset_path(aid)
        except ValueError:
            return None
        return output

    def backup(self, pid):
        target = self.project_dir(pid) / "backups" / f"project-{time.time_ns()}.db"
        with self.db(pid) as src, sqlite3.connect(target) as dest:
            src.backup(dest)
        return target
