"""已安装的本地 ComfyUI API 工作流适配；不安装或静默下载模型。"""
import copy
import json
from pathlib import PurePosixPath
import uuid

import httpx

from app.credentials import local_url
from app.providers import ProviderError


class ComfyUI:
    version = 'comfyui-2'

    def __init__(self, endpoint, workflows, client=None):
        if not local_url(endpoint):
            raise ValueError('ComfyUI 服务仅允许本机 loopback 地址')
        self.base = endpoint.rstrip('/')
        self.workflows = copy.deepcopy(workflows)
        self.client = client or httpx.Client(timeout=httpx.Timeout(120, connect=5), trust_env=False, follow_redirects=False)

    def request(self, method, path, **kwargs):
        try:
            response = self.client.request(method, self.base + path, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderError('LOCAL_MODEL_UNAVAILABLE', '未连接到本地 ComfyUI，请先启动服务并检查端口', True) from exc
        if response.status_code >= 500:
            raise ProviderError('LOCAL_MODEL_FAILED', '本地模型服务发生错误，请检查 ComfyUI 日志', True)
        if not response.is_success:
            raise ProviderError('LOCAL_MODEL_REJECTED', f'本地模型拒绝请求（HTTP {response.status_code}）')
        return response

    def json(self, method, path, **kwargs):
        try:
            data = self.request(method, path, **kwargs).json()
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except ValueError as exc:
            raise ProviderError('PROVIDER_MALFORMED', '本地模型返回了无效响应') from exc

    def diagnostics(self):
        try:
            stats = self.json('GET', '/system_stats')
            nodes = self.json('GET', '/object_info')
            checks = {}
            for kind in self.workflows:
                try:
                    self.validate(kind, nodes)
                    checks[kind] = {'ready': True}
                except ProviderError as exc:
                    checks[kind] = {'ready': False, 'error': str(exc)}
            return {'ready': True, 'devices': stats.get('devices', []), 'nodeCount': len(nodes), 'workflows': checks,
                    'installation': 'external', 'message': '使用已有本地运行时；模型和 custom nodes 由用户安装'}
        except ProviderError as exc:
            return {'ready': False, 'devices': [], 'nodeCount': 0, 'workflows': {}, 'error': str(exc)}

    def validate(self, kind, available):
        definition = self.workflows.get(kind)
        if not isinstance(definition, dict) or type(definition.get('version')) is not int or definition['version'] < 1:
            raise ProviderError('MODEL_UNAVAILABLE', '请先为该节点配置版本化 ComfyUI API 工作流模板')
        prompt, mappings = definition.get('prompt'), definition.get('mappings', {})
        if not isinstance(prompt, dict) or not prompt or not isinstance(mappings, dict):
            raise ProviderError('INVALID_INPUT', '需要 ComfyUI API 格式的 prompt 和字段 mappings')
        if len(json.dumps(definition)) > 1024**2:
            raise ProviderError('INVALID_INPUT', '本地工作流模板过大')
        mapped = set()
        for field, mapping in mappings.items():
            if not isinstance(mapping, dict) or not isinstance(mapping.get('node'), str) or not isinstance(mapping.get('input'), str):
                raise ProviderError('INVALID_INPUT', '工作流字段映射必须包含 node 和 input')
            if mapping['node'] not in prompt:
                raise ProviderError('INVALID_INPUT', '工作流字段映射引用不存在的节点')
            mapped.add((mapping['node'], mapping['input']))
        for nid, node in prompt.items():
            if not isinstance(node, dict) or not isinstance(node.get('inputs'), dict):
                raise ProviderError('INVALID_INPUT', '工作流节点结构无效')
            class_type = node.get('class_type')
            if class_type not in available:
                raise ProviderError('MODEL_UNAVAILABLE', f'本地缺少节点 {class_type}，请安装对应 custom node')
            for field, spec in available[class_type].get('input', {}).get('required', {}).items():
                if field not in node['inputs'] and (nid, field) not in mapped:
                    raise ProviderError('INVALID_INPUT', f'工作流节点 {class_type} 缺少参数 {field}')
                choices = spec[0] if isinstance(spec, list) and spec else None
                value = node['inputs'].get(field)
                if isinstance(choices, list) and isinstance(value, (str, int, float)) and (nid, field) not in mapped and value not in choices:
                    raise ProviderError('MODEL_UNAVAILABLE', f'本地缺少模型或选项 {value}，请安装并刷新模型列表')
        return definition

    def submit(self, kind, config, inputs):
        definition = self.validate(kind, self.json('GET', '/object_info'))
        mappings = definition.get('mappings', {})
        if config.get('prompt', '').strip() and 'prompt' not in mappings:
            raise ProviderError('INVALID_INPUT', '本地工作流未映射提示词，请添加 prompt 映射以使用上游文本')
        for field in ('image', 'video', 'audio'):
            values = inputs.get(field, [])
            mapping = mappings.get(field)
            used = {mapping.get('index', 0)} if mapping else set()
            if values and used != set(range(len(values))):
                raise ProviderError('INVALID_INPUT', f'本地工作流未映射全部 {field} 输入，请调整映射或参考素材数量')
        prompt = copy.deepcopy(definition['prompt'])
        for field, mapping in definition.get('mappings', {}).items():
            if field in ('image', 'audio', 'video'):
                values = inputs.get(field, [])
                index = mapping.get('index', 0)
                if type(index) is not int or index < 0 or index >= len(values):
                    raise ProviderError('INVALID_INPUT', f'本地工作流需要第 {index + 1} 个 {field} 输入')
                ext, mime = {'image': ('png', 'image/png'), 'audio': ('wav', 'audio/wav'), 'video': ('mp4', 'video/mp4')}[field]
                uploaded = self.json('POST', '/upload/image', files={'image': ('canvas-' + uuid.uuid4().hex + '.' + ext, values[index], mime)}, data={'type': 'input', 'overwrite': 'false'})
                value = uploaded.get('name')
                if not isinstance(value, str) or not value or PurePosixPath(value).name != value:
                    raise ProviderError('PROVIDER_MALFORMED', '本地输入上传结果无效')
                subfolder = uploaded.get('subfolder', '')
                if subfolder and ('..' in PurePosixPath(subfolder).parts or PurePosixPath(subfolder).is_absolute() or '\\' in subfolder or ':' in subfolder):
                    raise ProviderError('PROVIDER_MALFORMED', '本地输入上传路径无效')
                value = (subfolder + '/' if subfolder else '') + value
            else:
                if field not in config and 'default' not in mapping:
                    raise ProviderError('INVALID_INPUT', f'本地工作流需要参数 {field}')
                value = config.get(field, mapping.get('default'))
            prompt[mapping['node']]['inputs'][mapping['input']] = value
        result = self.json('POST', '/prompt', json={'prompt': prompt, 'client_id': uuid.uuid4().hex})
        if result.get('node_errors'):
            raise ProviderError('INVALID_INPUT', '本地工作流校验失败，请检查节点参数和模型文件')
        if not isinstance(result.get('prompt_id'), str) or not result['prompt_id']:
            raise ProviderError('SUBMIT_UNCERTAIN', '本地服务未返回 prompt_id，请核查历史后重试')
        return result['prompt_id']

    def history(self, external_id):
        if not isinstance(external_id, str) or '/' in external_id or '..' in external_id:
            raise ProviderError('INVALID_INPUT', '本地任务 ID 无效')
        return self.json('GET', '/history/' + external_id).get(external_id)

    def poll(self, external_id):
        record = self.history(external_id)
        if record is None:
            return 'QUEUED'
        status = record.get('status', {})
        if status.get('status_str') == 'error':
            return 'FAILED'
        if status.get('completed') is True and status.get('status_str') == 'success':
            return 'SUCCESS'
        return 'RUNNING'

    def fetch(self, external_id, kind, config, inputs):
        record = self.history(external_id)
        if not isinstance(record, dict):
            raise ProviderError('PROVIDER_MALFORMED', '本地任务尚无输出')
        expected = 'video' if kind.startswith('video.') else 'audio' if kind.startswith('audio.') else 'image'
        allowed = {'image': {'.png', '.jpg', '.jpeg', '.webp'}, 'video': {'.mp4', '.webm', '.mov'}, 'audio': {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}}[expected]
        result = []
        for output in record.get('outputs', {}).values():
            for category in ('images', 'gifs', 'videos', 'audio'):
                for item in output.get(category, []):
                    filename, folder = item.get('filename', ''), item.get('subfolder', '')
                    if not filename or PurePosixPath(filename).name != filename or '\\' in filename or ':' in filename or '..' in PurePosixPath(folder).parts or PurePosixPath(folder).is_absolute() or '\\' in folder or ':' in folder:
                        raise ProviderError('PROVIDER_MALFORMED', '本地输出文件路径无效')
                    if PurePosixPath(filename).suffix.lower() not in allowed:
                        continue
                    response = self.request('GET', '/view', params={'filename': filename, 'subfolder': folder, 'type': 'output'})
                    if not response.content or len(response.content) > 512 * 1024**2:
                        raise ProviderError('PROVIDER_MALFORMED', '本地输出为空或超过素材大小限制')
                    result.append((response.content, filename))
        if not result:
            raise ProviderError('PROVIDER_MALFORMED', f'本地工作流没有输出可用的 {expected} 素材')
        return result
