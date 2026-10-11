"""生成配置目录、严格校验和不含网络调用的请求构建。"""
import copy
import json
import math
import re
import secrets
from urllib.parse import urlparse

from generate_tool.rh_generate_workflow import build_request
from app.video_workflow import build_default_video_request

TEXT_KINDS = ('script.expand', 'shots.extract', 'character.extract', 'location.extract', 'prompt.video_expand')
MEDIA = ('image', 'video', 'audio')
KINDS = {'image.generate', 'image.variation', 'image.character', 'image.location', 'video.image_to_video', 'video.sound_effects', 'audio.tts'}
BUILTINS = [
    {'id': 'builtin-minimax-h3', 'name': 'MiniMax H3 · 自动匹配参考数量', 'kinds': ['video.image_to_video'], 'builtin': 'minimax_h3', 'version': 1, 'enabled': True},
    {'id': 'builtin-image2', 'name': 'Image2 · 自动匹配参考图', 'kinds': ['image.generate', 'image.variation', 'image.character', 'image.location'], 'builtin': 'image2', 'version': 1, 'enabled': True},
    {'id': 'builtin-ltx23', 'name': 'LTX 2.3 · 图生视频', 'kinds': ['video.image_to_video'], 'builtin': 'ltx23', 'version': 1, 'enabled': True},
    {'id': 'builtin-wan22', 'name': 'Wan 2.2 · 图生视频', 'kinds': ['video.image_to_video'], 'builtin': 'wan22', 'version': 1, 'enabled': True},
]


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', value) is not None


def string(value, label, limit=200):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(label + '不能为空或过长')


def validate_base(base):
    string(base, '文本服务地址', 2048)
    url = urlparse(base)
    local = url.scheme == 'http' and url.hostname in ('localhost', '127.0.0.1', '::1')
    if not url.hostname or url.username or url.password or url.query or url.fragment or not (url.scheme == 'https' or local):
        raise ValueError('文本服务地址必须为 HTTPS 或本机 HTTP，且不能包含凭据')
    if url.path.rstrip('/').endswith('/chat/completions'):
        raise ValueError('服务地址不应包含 /chat/completions')


def validate_profiles(data):
    for field in ('textServices', 'cloudWorkflows'):
        if field not in data:
            continue
        items = data[field]
        if not isinstance(items, list) or len(items) > 100:
            raise ValueError('生成配置必须为列表且不能超过 100 项')
        ids = set()
        for item in items:
            if not isinstance(item, dict) or not valid_id(item.get('id')) or item['id'] in ids or item['id'] == 'legacy' or item['id'].startswith('builtin-'):
                raise ValueError('配置 ID 无效、重复或使用了保留名称')
            ids.add(item['id'])
            string(item.get('name'), '配置名称', 100)
            if type(item.get('enabled')) is not bool:
                raise ValueError('配置启用状态无效')
            if field == 'textServices':
                if not item.keys() <= {'id', 'name', 'baseUrl', 'models', 'defaultModel', 'enabled'}:
                    raise ValueError('文本服务包含未知字段；密钥须单独保存')
                validate_base(item.get('baseUrl'))
                models = item.get('models')
                if not isinstance(models, list) or not 1 <= len(models) <= 100:
                    raise ValueError('请配置 1–100 个文本模型')
                for model in models:
                    string(model, '模型名称', 200)
                if len(set(models)) != len(models) or item.get('defaultModel') not in models:
                    raise ValueError('模型重复或默认模型不在列表中')
            else:
                validate_workflow(item)


def parse_workflow(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise ValueError('完整工作流 JSON 无法解析') from exc
    if not isinstance(value, dict) or not value:
        raise ValueError('完整工作流必须为非空 API 格式对象')
    try:
        if len(json.dumps(value, allow_nan=False)) > 1024 * 1024:
            raise ValueError('完整工作流不能超过 1 MB')
    except (TypeError, ValueError) as exc:
        raise ValueError('完整工作流过大或包含无效 JSON 值') from exc
    for node_id, node in value.items():
        string(node_id, '工作流节点 ID', 100)
        if not isinstance(node, dict) or not isinstance(node.get('inputs'), dict):
            raise ValueError('请使用 API 格式工作流，每个节点必须包含 inputs 和 class_type')
        string(node.get('class_type'), '节点 class_type', 200)
        for field, entry in node['inputs'].items():
            if any(word in field.lower() for word in ('apikey', 'api_key', 'token', 'password', 'secret', 'authorization')):
                raise ValueError('工作流中不能保存密钥字段')
            if isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], str) and type(entry[1]) is int:
                if entry[0] not in value or entry[1] < 0:
                    raise ValueError('工作流连接引用了不存在的节点或输出端口')
    return copy.deepcopy(value)


def validate_workflow(item):
    allowed = {'id', 'name', 'kinds', 'version', 'enabled', 'builtin', 'workflowId', 'workflow', 'nodeInfoList', 'mappings', 'resultNodes'}
    if not isinstance(item, dict) or not item.keys() <= allowed:
        raise ValueError('工作流包含未知字段')
    kinds = item.get('kinds')
    if not isinstance(kinds, list) or not kinds or any(not isinstance(k, str) or k not in KINDS for k in kinds):
        raise ValueError('工作流适用节点类型无效')
    if type(item.get('version')) is not int or item['version'] < 1:
        raise ValueError('工作流版本必须为正整数')
    if item.get('builtin'):
        original = next((w for w in BUILTINS if w['builtin'] == item['builtin']), None)
        if not original or not set(kinds) <= set(original['kinds']):
            raise ValueError('内置工作流与节点类型不兼容')
        if any(k in item for k in ('workflowId', 'workflow', 'nodeInfoList', 'mappings', 'resultNodes')):
            raise ValueError('内置工作流不能混入自定义模板')
        return
    graph = parse_workflow(item['workflow']) if 'workflow' in item else None
    if graph is None or item.get('workflowId'):
        string(item.get('workflowId'), 'RunningHub 工作流 ID', 100)
    results = item.get('resultNodes')
    if not isinstance(results, list) or not 1 <= len(results) <= 50:
        raise ValueError('请配置输出节点')
    for node in results:
        string(node, '输出节点 ID', 100)
        if graph is not None and node not in graph:
            raise ValueError('输出节点不在完整工作流中')
    fixed, mappings = item.get('nodeInfoList', []), item.get('mappings', [])
    if not isinstance(fixed, list) or not isinstance(mappings, list) or len(fixed) + len(mappings) > 200:
        raise ValueError('工作流参数数量或格式无效')
    targets = set()
    for entry in [*fixed, *mappings]:
        if not isinstance(entry, dict):
            raise ValueError('工作流参数必须为对象')
        string(entry.get('nodeId'), '输入节点 ID', 100)
        string(entry.get('fieldName'), '输入字段名', 100)
        target = (entry['nodeId'], entry['fieldName'])
        if graph is not None and (target[0] not in graph or target[1] not in graph[target[0]]['inputs']):
            raise ValueError('映射或固定参数的目标不在完整工作流 inputs 中')
        if target in targets:
            raise ValueError('同一节点字段不能重复设置或映射')
        targets.add(target)
    for entry in fixed:
        if set(entry) != {'nodeId', 'fieldName', 'fieldValue'} or not isinstance(entry['fieldValue'], (str, int, float, bool)) or isinstance(entry['fieldValue'], float) and not math.isfinite(entry['fieldValue']):
            raise ValueError('固定参数需包含 nodeId、fieldName 和标量 fieldValue')
        if any(word in entry['fieldName'].lower() for word in ('apikey', 'api_key', 'token', 'password', 'secret', 'authorization')):
            raise ValueError('工作流中不能保存密钥字段')
    for entry in mappings:
        if not entry.keys() <= {'source', 'nodeId', 'fieldName', 'index', 'required'} or entry.get('source') not in (*MEDIA, 'prompt', 'seconds', 'fps', 'seed'):
            raise ValueError('输入映射来源无效')
        if type(entry.get('index', 0)) is not int or not 0 <= entry.get('index', 0) < 9 or type(entry.get('required', True)) is not bool:
            raise ValueError('输入映射索引或必填状态无效')
        for kind in kinds:
            limit = {'image': 9, 'video': 3, 'audio': 3}.get(entry['source'], 8) if kind == 'video.image_to_video' else 8
            if entry.get('index', 0) >= limit:
                raise ValueError('输入映射索引超出该节点的参考素材上限')
            accepted = set(MEDIA) if kind == 'video.image_to_video' else {'image'} if kind in ('image.generate', 'image.variation', 'image.character', 'image.location') else {'audio'} if kind == 'audio.tts' else {'video'}
            if entry['source'] in MEDIA and entry['source'] not in accepted:
                raise ValueError('媒体映射与节点输入类型不兼容')
    if len(json.dumps(item)) > 1024 * 1024:
        raise ValueError('工作流模板过大')


def workflow_catalog(settings):
    return copy.deepcopy([workflow for workflow in [*BUILTINS, *settings.get('cloudWorkflows', [])]
                          if workflow.get('builtin') not in ('ltx23', 'wan22')])


def resolve_selection(settings, kind, config):
    if kind in TEXT_KINDS:
        sid = config.get('textServiceId') or 'legacy'
        if sid == 'legacy':
            return {'textServiceId': 'legacy', 'textCredential': 'text', 'textEndpoint': settings.get('textApiBase', ''), 'textModel': settings.get('textModel', '')}
        service = next((s for s in settings.get('textServices', []) if s['id'] == sid), None)
        if not service or not service['enabled']:
            raise ValueError('所选文本服务不存在或已停用，请重新选择')
        model = config.get('textModel') or service['defaultModel']
        if model not in service['models']:
            raise ValueError('所选模型不在该文本服务的模型列表中')
        return {'textServiceId': sid, 'textCredential': 'text-' + sid, 'textEndpoint': service['baseUrl'], 'textModel': model}
    wid = config.get('workflowId')
    if config.get('provider') == 'comfyui':
        return {}
    if kind == 'video.image_to_video' and not wid:
        wid = 'builtin-minimax-h3'
    if not wid:
        return {}
    workflow = next((w for w in workflow_catalog(settings) if w['id'] == wid), None)
    if not workflow or not workflow['enabled'] or kind not in workflow['kinds']:
        raise ValueError('所选工作流不存在、已停用或不适用于该节点')
    return {'cloudWorkflow': workflow}


def build_workflow_request(kind, config, inputs, workflow=None):
    if not workflow:
        return build_request(kind, config, inputs)
    validate_workflow(workflow)
    if kind not in workflow['kinds']:
        raise ValueError('工作流与节点类型不兼容')
    if kind == 'audio.tts' and inputs.get('audio') and not config.get('voiceAuthorized'):
        raise ValueError('使用参考声音前须确认已获得授权')
    if workflow.get('builtin'):
        if workflow['builtin'] == 'minimax_h3':
            request = build_default_video_request(config, inputs)
            request['workflow'] = parse_workflow(request['workflow'])
            return request
        return build_request(kind, {**config, 'model': workflow['builtin']}, inputs)
    if config.get('prompt', '').strip() and not any(m['source'] == 'prompt' for m in workflow.get('mappings', [])):
        raise ValueError('工作流未映射提示词，无法使用上游文本；请添加 prompt 输入映射')
    values, used = [], {port: set() for port in MEDIA}
    for mapping in workflow.get('mappings', []):
        source = mapping['source']
        entry = {'nodeId': mapping['nodeId'], 'fieldName': mapping['fieldName']}
        if source in MEDIA:
            index = mapping.get('index', 0)
            assets = inputs.get(source, [])
            if index >= len(assets):
                if mapping.get('required', True):
                    raise ValueError(f'工作流缺少 {source} 第 {index + 1} 项输入')
                continue
            used[source].add(index)
            entry.update(fieldValue=assets[index], _mediaType=source)
        else:
            entry['fieldValue'] = secrets.randbelow(2147483647) if source == 'seed' else config.get(source, {'prompt': '', 'seconds': 5, 'fps': 25}[source])
        values.append(entry)
    for port in MEDIA:
        if used[port] != set(range(len(inputs.get(port, [])))):
            raise ValueError(f'工作流未映射全部 {port} 输入，请调整映射或参考素材数量')
    return {**({'workflow': parse_workflow(workflow['workflow'])} if 'workflow' in workflow else {}),
            'workflowId': workflow.get('workflowId'), 'nodeInfoList': copy.deepcopy(workflow.get('nodeInfoList', [])),
            'user_data': values, 'result_node': list(workflow['resultNodes'])}


def generation_options(settings):
    config = settings.load()
    legacy = {'id': 'legacy', 'name': '默认文本服务（兼容原配置）', 'baseUrl': config['textApiBase'],
              'models': [config['textModel']] if config['textModel'] else [], 'defaultModel': config['textModel'], 'enabled': True}
    services = [legacy, *copy.deepcopy(config.get('textServices', []))]
    for service in services:
        credential = 'text' if service['id'] == 'legacy' else 'text-' + service['id']
        service['ready'] = bool(service['enabled'] and service['baseUrl'] and service['models'] and settings.key(credential))
    return {'workflows': workflow_catalog(config), 'textServices': services}
