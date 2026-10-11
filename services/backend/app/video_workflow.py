"""按实际参考素材数量适配用户提供的 MiniMax H3 完整工作流。"""
import copy
import math
import secrets

from generate_tool import workflow_json_new


def build_default_video_request(config, inputs):
    images = inputs.get('image', [])
    audios = inputs.get('audio', [])
    videos = inputs.get('video', [])
    if not 1 <= len(images) <= 9:
        raise ValueError('默认 MiniMax H3 工作流需要 1–9 张参考图片')
    if len(audios) > 1 or len(videos) > 1 or (audios and videos):
        raise ValueError('workflow_json_new.py 仅提供单音频或单视频模板；请使用最多 1 段音频或 1 段视频，更多参考需选择相应自定义工作流')
    seconds = config.get('seconds', 5)
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 1 <= seconds <= 30:
        raise ValueError('生成时长须为 1–30 秒')
    suffix = '_1_audio' if audios else '_1_video' if videos else ''
    name = f'minimax_h3_{len(images)}_image{suffix}_json'
    graph = copy.deepcopy(getattr(workflow_json_new, name))
    # 部分模板携带未接入输出的示例加载器，不能将这些文件提交到云端。
    needed, pending = set(), ['271']
    while pending:
        node_id = pending.pop()
        if node_id in needed:
            continue
        needed.add(node_id)
        for value in graph[node_id]['inputs'].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and type(value[1]) is int:
                pending.append(value[0])
    graph = {node_id: node for node_id, node in graph.items() if node_id in needed}
    graph['115']['inputs']['megapixels'] = 0.4
    graph['138']['inputs']['value'] = ''
    conditioning = graph['136']['inputs']
    values = [
        {'nodeId': '138', 'fieldName': 'value', 'fieldValue': config.get('prompt', '')},
        {'nodeId': '132', 'fieldName': 'value', 'fieldValue': seconds},
        {'nodeId': '129', 'fieldName': 'noise_seed', 'fieldValue': secrets.randbelow(2147483647)},
    ]
    for index, data in enumerate(images):
        node_id = conditioning[f'ref_images.ref_image_{index}'][0]
        graph[node_id]['inputs']['image'] = ''
        values.append({'nodeId': node_id, 'fieldName': 'image', 'fieldValue': data, '_mediaType': 'image'})
    if audios or videos:
        port = 'audio' if audios else 'video'
        node_id = conditioning['ref_audios.ref_audio_0'][0]
        graph[node_id]['inputs'][port] = ''
        values.append({'nodeId': node_id, 'fieldName': port, 'fieldValue': (audios or videos)[0], '_mediaType': port})
    return {'workflow': graph, 'nodeInfoList': [], 'user_data': values, 'result_node': ['271']}
