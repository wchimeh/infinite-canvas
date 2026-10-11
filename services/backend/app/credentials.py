"""应用级公开设置与 Windows Credential Manager，绝不落盘明文密钥。"""
import copy
import ctypes
from ctypes import wintypes
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import uuid

from app.generation_profiles import validate_profiles, valid_id

ENV_KEYS = {'runninghub': 'RUNNINGHUB_API_KEY', 'text': 'TEXT_API_KEY'}
DEFAULTS = {'textApiBase': '', 'textModel': '', 'comfyUrl': 'http://127.0.0.1:8188', 'comfyWorkflows': {},
            'concurrency': {'image': 2, 'video': 1, 'audio': 1, 'text': 1}, 'pricing': {}, 'textServices': [], 'cloudWorkflows': []}


class WindowsVault:
    def __init__(self, namespace='InfiniteCanvas'):
        self.namespace = namespace
        self.available = os.name == 'nt'
        if not self.available:
            return

        class Credential(ctypes.Structure):
            _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
                        ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
                        ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
                        ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
        self.Credential = Credential
        self.api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
        self.api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(Credential))]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]
        self.api.CredFree.restype = None

    def get(self, name):
        if not self.available:
            return ''
        pointer = ctypes.POINTER(self.Credential)()
        if not self.api.CredReadW(self.namespace + '/' + name, 1, 0, ctypes.byref(pointer)):
            error = ctypes.get_last_error()
            if error == 1168:
                return ''
            raise ValueError(f'系统凭据读取失败（Windows {error}）')
        try:
            blob = pointer.contents
            return ctypes.string_at(blob.CredentialBlob, blob.CredentialBlobSize).decode('utf-8')
        finally:
            self.api.CredFree(pointer)

    def set(self, name, value):
        if not self.available:
            raise ValueError('系统凭据保管目前仅支持 Windows；其他平台请使用环境变量')
        data = value.encode('utf-8')
        if not 0 < len(data) <= 2560:
            raise ValueError('密钥为空或超过系统凭据大小限制')
        buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        credential = self.Credential()
        credential.Type, credential.Persist = 1, 2
        credential.TargetName = self.namespace + '/' + name
        credential.UserName = 'InfiniteCanvas'
        credential.CredentialBlobSize = len(data)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        if not self.api.CredWriteW(ctypes.byref(credential), 0):
            raise ValueError(f'系统凭据保存失败（Windows {ctypes.get_last_error()}）')

    def delete(self, name):
        if self.available and not self.api.CredDeleteW(self.namespace + '/' + name, 1, 0):
            error = ctypes.get_last_error()
            if error != 1168:
                raise ValueError(f'系统凭据撤销失败（Windows {error}）')


def local_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ('http', 'https') and parsed.hostname in ('127.0.0.1', 'localhost', '::1') and not parsed.username and not parsed.password


class Settings:
    def __init__(self, root=None, vault=None):
        self.root = Path(root or os.getenv('CANVAS_CONFIG_DIR') or Path(os.getenv('LOCALAPPDATA', str(Path.home() / '.config'))) / 'InfiniteCanvas').resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'settings.json'
        namespace = 'InfiniteCanvas/' + hashlib.sha256(str(self.root).encode()).hexdigest()[:16]
        self.vault = vault if vault is not None else WindowsVault(namespace)

    def load(self):
        data = copy.deepcopy(DEFAULTS)
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding='utf-8'))
                self.validate(saved)
                data.update(saved)
            except (ValueError, TypeError) as exc:
                raise ValueError('应用设置文件损坏，请恢复备份或重新配置') from exc
        limits = {**DEFAULTS['concurrency'], **data.get('concurrency', {})}
        limits.setdefault('media', min(8, limits['image'] + limits['video']))
        data['concurrency'] = limits
        for field, env in [('textApiBase', 'TEXT_API_BASE'), ('textModel', 'TEXT_MODEL')]:
            if os.getenv(env):
                data[field] = os.getenv(env)
        return data

    def key(self, name):
        if name not in ENV_KEYS and not (name.startswith('text-') and valid_id(name[5:])):
            raise ValueError('不支持的凭据名称')
        return (os.getenv(ENV_KEYS[name]) if name in ENV_KEYS else '') or self.vault.get(name)

    def set_key(self, name, value):
        configured = {'text-' + s['id'] for s in self.load()['textServices']}
        if name not in ENV_KEYS and name not in configured or not isinstance(value, str) or not value.strip():
            raise ValueError('凭据名称或密钥无效')
        self.vault.set(name, value.strip())

    def delete_key(self, name):
        if name not in ENV_KEYS and not (name.startswith('text-') and valid_id(name[5:])):
            raise ValueError('不支持的凭据名称')
        self.vault.delete(name)

    def public(self):
        data = self.load()
        data['credentials'] = {name: {'configured': bool(self.key(name)),
                                      'source': 'environment' if os.getenv(env) else 'vault' if self.vault.get(name) else 'none'}
                               for name, env in ENV_KEYS.items()}
        for service in data['textServices']:
            name = 'text-' + service['id']
            configured = bool(self.key(name))
            data['credentials'][name] = {'configured': configured, 'source': 'vault' if configured else 'none'}
        data['vaultAvailable'] = getattr(self.vault, 'available', True)
        return data

    @staticmethod
    def validate(data):
        if not isinstance(data, dict) or not data.keys() <= DEFAULTS.keys():
            raise ValueError('设置包含未知字段或凭据；密钥请使用系统凭据接口')
        validate_profiles(data)
        for key in ('textApiBase', 'textModel', 'comfyUrl'):
            if key in data and (not isinstance(data[key], str) or len(data[key]) > 2048):
                raise ValueError('服务地址或模型名称无效')
        base = data.get('textApiBase')
        if base:
            parsed = urlparse(base)
            if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or not (parsed.scheme == 'https' or local_url(base)):
                raise ValueError('文本服务必须使用 HTTPS 或本地 HTTP 地址，不允许地址中包含凭据')
        if 'comfyUrl' in data and not local_url(data['comfyUrl']):
            raise ValueError('ComfyUI 服务仅允许本机 loopback 地址')
        if 'concurrency' in data:
            limits = data['concurrency']
            if not isinstance(limits, dict) or not limits.keys() <= {'media', 'image', 'video', 'audio', 'text'} or any(type(v) is not int or not 1 <= v <= 8 for v in limits.values()):
                raise ValueError('每类并发必须是 1–8 的整数')
        if 'pricing' in data:
            rules = data['pricing']
            if not isinstance(rules, dict) or len(rules) > 100:
                raise ValueError('价格表无效')
            for model, rule in rules.items():
                try:
                    amount = Decimal(str(rule['amount']))
                    if not amount.is_finite() or amount < 0 or rule['unit'] not in ('task', 'second') or rule['currency'] not in ('CNY', 'USD') or len(model) > 300:
                        raise ValueError('价格规则无效')
                except (KeyError, TypeError, InvalidOperation) as exc:
                    raise ValueError('价格规则无效') from exc
        if 'comfyWorkflows' in data:
            if not isinstance(data['comfyWorkflows'], dict) or len(json.dumps(data['comfyWorkflows'])) > 1024**2:
                raise ValueError('本地工作流模板无效或过大')

    def save(self, changes):
        self.validate(changes)
        current = self.load()
        for key in ('concurrency', 'pricing', 'comfyWorkflows'):
            if key in changes:
                changes = {**changes, key: {**current[key], **changes[key]} if key == 'concurrency' else changes[key]}
        current.update(changes)
        self.validate(current)
        temporary = self.root / ('settings-' + uuid.uuid4().hex + '.partial')
        try:
            with temporary.open('x', encoding='utf-8') as stream:
                json.dump(current, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.public()
