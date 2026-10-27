"""Persistent project data location, separate from service settings and credentials."""
import json
from contextlib import suppress
import os
from pathlib import Path
import tempfile
import threading
import uuid


class ProjectStorage:
    def __init__(self, config_root):
        self.path = Path(config_root) / 'project-storage.json'
        self.lock = threading.Lock()

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or not isinstance(data.get('directory'), str):
                raise ValueError()
            return data
        except (OSError, ValueError) as exc:
            raise ValueError('项目存储配置无法读取，请恢复 project-storage.json 或在设置中重新指定目录') from exc

    @staticmethod
    def validate(value):
        if not isinstance(value, str) or not value.strip() or '\x00' in value:
            raise ValueError('请输入项目数据的完整绝对路径')
        path = Path(value.strip()).expanduser()
        if not path.is_absolute() or '..' in path.parts:
            raise ValueError('项目数据目录必须是绝对路径，不能包含 ..')
        path = path.resolve()
        if path == Path(path.anchor):
            raise ValueError('请选择专用文件夹，不能直接使用磁盘根目录')
        try:
            path.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=path):
                pass
        except OSError as exc:
            raise ValueError('目录无法创建或写入，请检查路径、磁盘和权限') from exc
        return path

    def save(self, value):
        directory = self.validate(value)
        with self.lock:
            temporary = self.path.with_name('project-storage-' + uuid.uuid4().hex + '.partial')
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with temporary.open('x', encoding='utf-8') as stream:
                    json.dump({'directory': str(directory)}, stream, ensure_ascii=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            except OSError as exc:
                raise ValueError('数据目录配置写入失败，请检查系统配置目录权限或磁盘空间；上次保存的路径未更改') from exc
            finally:
                with suppress(OSError):
                    temporary.unlink(missing_ok=True)
        return directory

    def resolve(self, default):
        saved = self.load()
        return self.validate(saved['directory']) if saved else Path(default).resolve()

    def status(self, current, startup_error=''):
        try:
            configured = self.load().get('directory', str(current))
        except ValueError as exc:
            configured, startup_error = str(current), str(exc)
        return {'currentDirectory': str(current), 'nextDirectory': configured,
                'restartRequired': Path(configured) != Path(current), 'startupError': startup_error}
