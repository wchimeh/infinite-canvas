"""Adapt the supplied WenWu 05 workflow without changing its model/sampler chain."""
import copy
import math
import secrets

from app.video_workflow import ASPECT_RATIOS
from generate_tool.minimax_h3_combat import WORKFLOW


def build_combat_video_request(config, inputs):
    if not 1 <= len(inputs.get('image', [])) <= 9:
        raise ValueError('生成视频-武打需要1–9张参考图片')
    if any(len(inputs.get(port, [])) > 3 for port in ('audio', 'video')):
        raise ValueError('生成视频-武打最多支持3段音频和3段视频')
    if any(values for port, values in inputs.items() if port not in ('image', 'audio', 'video')):
        raise ValueError('生成视频-武打仅支持图片、参考音频和参考视频')
    options = config.get('combatH3', {})
    if not isinstance(options, dict):
        raise ValueError('武打生成参数必须为对象')

    def number(key, default, low, high, integer=False):
        value = options.get(key, default)
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not low <= value <= high or (integer and type(value) is not int)):
            raise ValueError(f'武打参数 {key} 须为{low}–{high}的' + ('整数' if integer else '数字'))
        return value

    seconds = config.get('seconds', 8)
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 1 <= seconds <= 30:
        raise ValueError('生成时长须为1–30秒')
    ratio = options.get('aspectRatio', '16:9 (Widescreen)')
    if ratio not in ASPECT_RATIOS:
        raise ValueError('请选择有效画面比例')
    mode = options.get('seedMode', 'random')
    if mode not in ('random', 'fixed'):
        raise ValueError('种子模式须为随机或固定')
    seed = number('seed', 0, 0, 9007199254740991, True) if mode == 'fixed' else secrets.randbelow(9007199254740992)
    graph = copy.deepcopy(WORKFLOW)
    graph['263']['inputs']['text'] = config.get('prompt', '')
    graph['259']['inputs']['value'] = seconds
    graph['252']['inputs'].update(aspect_ratio=ratio, megapixels=number('megapixels', 0.5, 0.01, 16))
    steps = number('steps', 10, 2, 1000, True)
    graph['261']['inputs']['steps'] = steps
    graph['397']['inputs'].update(seed=seed, cfg=number('cfg', 1, 0, 20),
                                  transition_step=number('transitionStep', 6, 1, steps - 1, True))
    for node, key, default, high in [('342', 'combatStrength', 0.35, 2), ('344', 'motionRepairStrength', 0.35, 2),
                                      ('345', 'fightFlowStrength', 0.35, 2), ('343', 'speedStrength', 1, 4)]:
        graph[node]['inputs']['strength_model'] = number(key, default, 0, high)
    uploads = []
    conditioning = graph['265']['inputs']
    for port, limit in [('image', 9), ('audio', 3), ('video', 3)]:
        values = inputs.get(port, [])
        for index in range(limit):
            key = f'ref_{port}s.ref_{port}_{index}'
            loader = conditioning[key][0]
            if index >= len(values):
                del conditioning[key]
                continue
            graph[loader]['inputs'][port] = ''
            if port == 'video':
                graph[loader]['inputs']['force_rate'] = 24
            uploads.append({'nodeId': loader, 'fieldName': port, 'fieldValue': values[index], '_mediaType': port})
    needed, pending = set(), ['364']
    while pending:
        node = pending.pop()
        if node in needed:
            continue
        needed.add(node)
        for value in graph[node]['inputs'].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and type(value[1]) is int:
                pending.append(value[0])
    return {'workflow': {key: value for key, value in graph.items() if key in needed},
            'nodeInfoList': [], 'user_data': uploads, 'result_node': ['364']}
