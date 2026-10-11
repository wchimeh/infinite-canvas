"""一致性迁移包与无素材画布模板；所有导入都创建独立项目。"""
import copy
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile
import uuid
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from app.graph import validate_graph
from app.store import encode

MAX_SIZE = 2 * 1024**3
SECRET_KEYS = {'apikey', 'api_key', 'key', 'token', 'password', 'authorization', 'credentials', 'secret', 'text_api_key', 'runninghub_api_key'}


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if k.lower() not in SECRET_KEYS}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def safe_name(name):
    path = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or '\x00' in name:
        raise ValueError('项目包文件路径无效')
    return path


def export_project(store, pid):
    store.document(pid, 'project')
    with tempfile.TemporaryDirectory(prefix='canvas-package-') as tmp:
        db = Path(tmp) / 'project.db'
        with store.db(pid) as source, closing(sqlite3.connect(db)) as target:
            source.backup(target)
        with closing(sqlite3.connect(db)) as con:
            con.execute('PRAGMA journal_mode=DELETE')
            for table in ('tasks', 'runs', 'events'):
                con.execute(f'DELETE FROM {table}')
            con.execute('DROP TABLE IF EXISTS cost_reservations')
            con.execute("DELETE FROM documents WHERE key LIKE 'export:%' OR key LIKE 'preview:%' OR key LIKE 'cost:%'")
            con.execute('DELETE FROM assets WHERE deleted=1')
            assets = [json.loads(row[0]) for row in con.execute('SELECT body FROM assets')]
            for key, body in con.execute('SELECT key, body FROM documents').fetchall():
                clean = sanitize(json.loads(body))
                if key == 'project':
                    clean['settings']['cloudEnabled'] = False
                if key == 'canvas':
                    for node in clean['nodes']:
                        for field in ('output', 'error', 'modifiedAt'):
                            node.get('data', {}).pop(field, None)
                        node['data']['status'] = 'idle'
                con.execute('UPDATE documents SET body=? WHERE key=?', (encode(clean), key))
            for asset in assets:
                con.execute('UPDATE assets SET body=? WHERE id=?', (encode(sanitize(asset)), asset['id']))
            con.commit()
            # 删除页必须重写，避免 SQLite 空闲页继续携带旧密钥/任务数据。
            con.execute('VACUUM')
        out = io.BytesIO()
        hashes = {}
        with ZipFile(out, 'w', ZIP_DEFLATED) as package:
            def add(name, data):
                safe_name(name)
                if name in hashes:
                    return
                hashes[name] = hashlib.sha256(data).hexdigest()
                package.writestr(name, data)
            add('project.db', db.read_bytes())
            for asset in assets:
                data = store.asset_path(asset['id']).read_bytes()
                if hashlib.sha256(data).hexdigest() != asset['sha256']:
                    raise ValueError('素材 hash 校验失败，不能导出项目')
                add(asset['path'], data)
            for path in (store.project_dir(pid) / 'exports').glob('*'):
                if path.is_file() and path.suffix in ('.mp4', '.srt', '.json'):
                    add('exports/' + path.name, path.read_bytes())
            package.writestr('manifest.json', json.dumps({'format': 'infinite-canvas-project', 'schemaVersion': 1,
                                                         'projectId': pid, 'files': hashes}, ensure_ascii=False))
        return out.getvalue()


def remap(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [remap(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: remap(item, mapping) for key, item in value.items()}
    return value


def import_project(store, data):
    if len(data) > MAX_SIZE:
        raise ValueError('项目包超过大小限制')
    created = None
    try:
        with ZipFile(io.BytesIO(data)) as package, tempfile.TemporaryDirectory(prefix='canvas-import-') as tmp:
            entries = package.infolist()
            names = [entry.filename for entry in entries]
            if len(entries) > 10000 or len(names) != len(set(names)) or sum(e.file_size for e in entries) > MAX_SIZE:
                raise ValueError('项目包数量或大小超限')
            for entry in entries:
                safe_name(entry.filename)
                if entry.is_dir() or entry.flag_bits & 1 or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('项目包不能包含链接、目录或加密文件')
            manifest = json.loads(package.read('manifest.json'))
            files = manifest.get('files', {})
            if manifest.get('format') != 'infinite-canvas-project' or manifest.get('schemaVersion') != 1 or not isinstance(files, dict):
                raise ValueError('项目包格式或版本不支持')
            if set(names) != {'manifest.json', *files} or 'project.db' not in files:
                raise ValueError('项目包文件清单不一致')
            extracted = {}
            for name, digest in files.items():
                if name != 'project.db' and not name.startswith(('assets/', 'exports/')):
                    raise ValueError('项目包文件类型不允许')
                contents = package.read(name)
                if hashlib.sha256(contents).hexdigest() != digest:
                    raise ValueError('项目包 hash 校验失败')
                extracted[name] = contents
            db = Path(tmp) / 'project.db'
            db.write_bytes(extracted['project.db'])
            with closing(sqlite3.connect(f'{db.as_uri()}?mode=ro', uri=True)) as con:
                # 禁止读取包数据库中的视图/触发器，关闭 trusted_schema。
                con.execute('PRAGMA trusted_schema=OFF')
                kinds = dict(con.execute('SELECT name,type FROM sqlite_master'))
                if kinds.get('documents') != 'table' or kinds.get('assets') != 'table' or 'trigger' in kinds.values():
                    raise ValueError('项目数据库结构无效')
                if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('项目数据库校验失败')
                documents = {key: sanitize(json.loads(body)) for key, body in con.execute('SELECT key,body FROM documents')
                             if key in ('project', 'canvas', 'timeline', 'people')}
                assets = [sanitize(json.loads(row[0])) for row in con.execute('SELECT body FROM assets WHERE deleted=0')]
            if set(documents) != {'project', 'canvas', 'timeline', 'people'}:
                raise ValueError('项目数据库缺少必需记录')
            old_pid = documents['project']['id']
            if not re.fullmatch('[a-f0-9]{32}', old_pid):
                raise ValueError('项目 ID 无效')
            for asset in assets:
                if asset.get('projectId') != old_pid or asset.get('path') not in extracted:
                    raise ValueError('项目素材文件缺失')
                if hashlib.sha256(extracted[asset['path']]).hexdigest() != asset['sha256']:
                    raise ValueError('素材 hash 校验失败')
            errors = validate_graph(documents['canvas'].get('nodes'), documents['canvas'].get('edges'))['errors']
            if errors:
                raise ValueError('；'.join(errors))
            created = store.create_project(documents['project']['name'])
            new_pid = created['id']
            mapping = {old_pid: new_pid}
            for asset in assets:
                mapping[asset['id']] = store.add_asset(new_pid, extracted[asset['path']], asset['name'], asset.get('nodeId'))['id']
            for key, body in documents.items():
                body = remap(body, mapping)
                if key == 'project':
                    body['id'] = new_pid
                    body['settings']['cloudEnabled'] = False
                if key == 'canvas':
                    for node in body['nodes']:
                        node['selected'] = False
                        node['data']['status'] = 'idle'
                        for field in ('output', 'error', 'modifiedAt'):
                            node['data'].pop(field, None)
                store.put_document(new_pid, key, body)
            for name, contents in extracted.items():
                if name.startswith('exports/'):
                    target = store.project_dir(new_pid) / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(contents)
            return store.document(new_pid, 'project')
    except (BadZipFile, KeyError, TypeError, sqlite3.Error, json.JSONDecodeError) as exc:
        if created:
            shutil.rmtree(store.project_dir(created['id']))
        raise ValueError('项目包损坏或结构无效') from exc
    except Exception:
        if created:
            shutil.rmtree(store.project_dir(created['id']))
        raise


def export_template(store, pid):
    canvas = sanitize(copy.deepcopy(store.canvas(pid)))
    canvas.pop('version', None)
    for node in canvas['nodes']:
        node['selected'] = False
        node['data']['status'] = 'idle'
        for key in ('output', 'error', 'modifiedAt'):
            node['data'].pop(key, None)
        for key in ('assetId', 'referenceIds', 'approved'):
            node['data'].get('config', {}).pop(key, None)
    return {'format': 'infinite-canvas-template', 'schemaVersion': 1, 'canvas': canvas}


def import_template(store, pid, template):
    if template.get('format') != 'infinite-canvas-template' or template.get('schemaVersion') != 1:
        raise ValueError('画布模板格式或版本无效')
    incoming = sanitize(copy.deepcopy(template['canvas']))
    errors = validate_graph(incoming.get('nodes'), incoming.get('edges'))['errors']
    if errors:
        raise ValueError('；'.join(errors))
    canvas = store.canvas(pid)
    mapping = {node['id']: str(uuid.uuid4()) for node in incoming['nodes']}
    groups = {node['data']['groupId']: str(uuid.uuid4()) for node in incoming['nodes'] if node['data'].get('groupId')}
    for node in incoming['nodes']:
        if node['data'].get('groupId'):
            node['data']['groupId'] = groups[node['data']['groupId']]
    incoming = remap(incoming, mapping)
    for node in incoming['nodes']:
        node['selected'] = False
        node['data']['status'] = 'idle'
        node['position']['x'] += 80
        node['position']['y'] += 80
        for key in ('output', 'error', 'modifiedAt'):
            node['data'].pop(key, None)
        for key in ('assetId', 'referenceIds', 'approved'):
            node['data'].get('config', {}).pop(key, None)
    for edge in incoming['edges']:
        edge['id'] = str(uuid.uuid4())
    canvas['nodes'].extend(incoming['nodes'])
    canvas['edges'].extend(incoming['edges'])
    return store.save_canvas(pid, canvas, canvas['version'])
