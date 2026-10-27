"""按实际参考素材数量适配用户提供的 MiniMax H3 完整工作流。"""
import copy
import math
import secrets
import hashlib

from generate_tool.minimax_h3_all import WORKFLOW

ASPECT_RATIOS = ('1:1 (Square)', '2:3 (Portrait Photo)', '3:2 (Photo)',
                 '3:4 (Portrait Standard)', '4:3 (Standard)', '9:16 (Portrait Widescreen)',
                 '16:9 (Widescreen)', '21:9 (Ultrawide)')


def minimax_parameters(config):
    options = config.get('minimaxH3', {})
    if not isinstance(options, dict):
        raise ValueError('MiniMax H3 参数必须为对象')
    ratio = options.get('aspectRatio', '16:9 (Widescreen)')
    if not isinstance(ratio, str) or ratio not in ASPECT_RATIOS:
        raise ValueError('MiniMax H3 画面比例须从工作流支持的八种比例中选择')
    def number(key, default, minimum, maximum, label, integer=False):
        value = options.get(key, default)
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not minimum <= value <= maximum or (integer and type(value) is not int)):
            raise ValueError(f'MiniMax H3 {label}须为 {minimum}–{maximum} 的' + ('整数' if integer else '数字'))
        return value
    megapixels = number('megapixels', 0.4, 0.01, 16, '百万像素数')
    multiple = number('multiple', 32, 1, 1024, '尺寸倍数', True)
    steps = number('steps', 8, 1, 1000, '采样步数', True)
    mode = options.get('seedMode', 'random')
    if mode not in ('random', 'fixed'):
        raise ValueError('MiniMax H3 种子模式须为随机或固定')
    seed = number('seed', None, 0, 2147483646, '种子', True) if mode == 'fixed' else secrets.randbelow(2147483647)
    return {'aspect_ratio': ratio.strip(), 'megapixels': megapixels, 'multiple': multiple}, steps, seed


def build_default_video_request(config, inputs):
    groups = [('image', 9, 'ref_images.ref_image_', 0), ('video', 3, 'ref_videos.ref_video_', 0),
              ('audio', 3, 'ref_audios.ref_audio_', 0), ('video_audio', 3, 'ref_video_audios.ref_video_audio_', 0)]
    for port, limit, _, _ in groups:
        if len(inputs.get(port, [])) > limit:
            raise ValueError(f'MiniMax H3 最多支持 {limit} 个 {port} 参考素材')
    if not any(inputs.get(port) for port, _, _, _ in groups):
        raise ValueError('MiniMax H3 至少需要一个图片、视频、音频或视频音频参考')
    audio_indices = config.get('_videoAudioVideoIndices', list(range(len(inputs.get('video_audio', [])))))
    if (not isinstance(audio_indices, list) or len(audio_indices) != len(inputs.get('video_audio', []))
            or any(type(i) is not int or not 0 <= i < 3 for i in audio_indices)
            or len(set(audio_indices)) != len(audio_indices)):
        raise ValueError('视频音频槽位无效')
    seconds = config.get('seconds', 5)
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 1 <= seconds <= 30:
        raise ValueError('生成时长须为 1–30 秒')
    graph = copy.deepcopy(WORKFLOW)
    resolution, steps, seed = minimax_parameters(config)
    graph['115']['inputs'].update(resolution)
    graph['124']['inputs']['steps'] = steps
    graph['144']['inputs']['prompt'] = ''
    conditioning = graph['136']['inputs']
    values = [
        {'nodeId': '144', 'fieldName': 'prompt', 'fieldValue': config.get('prompt', '')},
        {'nodeId': '132', 'fieldName': 'value', 'fieldValue': seconds},
        {'nodeId': '129', 'fieldName': 'noise_seed', 'fieldValue': seed},
    ]
    # 配套音轨使用视频槽号；可复用音频文件，但不能覆盖视频画面加载器。
    used_loaders, media_loaders = set(), {}
    for port, limit, prefix, output in groups:
        supplied = dict(zip(audio_indices, inputs.get(port, []))) if port == 'video_audio' else dict(enumerate(inputs.get(port, [])))
        for index in range(limit):
            key = prefix + str(index)
            source = conditioning[key][0]
            if index not in supplied:
                del conditioning[key]
                continue
            data = supplied[index]
            media_type = 'audio' if port == 'video_audio' else port
            digest = (media_type, hashlib.sha256(data).hexdigest()) if media_type in ('video', 'audio') else None
            if digest in media_loaders:
                conditioning[key] = [media_loaders[digest], output]
                continue
            node_id = source
            if node_id in used_loaders:
                node_id = str(max(int(n) for n in graph) + 1)
                graph[node_id] = copy.deepcopy(graph[source])
            if port == 'video_audio':
                graph[node_id] = copy.deepcopy(WORKFLOW['180'])
            used_loaders.add(node_id)
            conditioning[key] = [node_id, output]
            graph[node_id]['inputs'][media_type] = ''
            if digest is not None:
                media_loaders[digest] = node_id
            values.append({'nodeId': node_id, 'fieldName': media_type, 'fieldValue': data, '_mediaType': media_type})
    # 从实际输出回溯，只保留依赖图，移除未使用的示例加载器。
    needed, pending = set(), ['92']
    while pending:
        node_id = pending.pop()
        if node_id in needed:
            continue
        needed.add(node_id)
        for value in graph[node_id]['inputs'].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and type(value[1]) is int:
                pending.append(value[0])
    graph = {node_id: node for node_id, node in graph.items() if node_id in needed}
    return {'workflow': graph, 'nodeInfoList': [], 'user_data': values, 'result_node': ['92']}
