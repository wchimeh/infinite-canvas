"""Deterministic visual direction, independent of model-generated prose."""

STYLES = {
    'live_action': '真人实拍（live-action photorealistic）：真实演员、自然人体比例、真实皮肤纹理、摄影光照与现实材质；不要动漫、卡通、插画、二次元或塑料感CG人物。奇幻题材也使用真人影视特效呈现。',
    'anime': '二维动漫：统一二维动画美术、线条和赛璐璐着色，保持人物与环境风格一致。',
    'animation_3d': '三维动画：统一三维动画人物造型、材质和灯光，保持人物与环境风格一致。',
}


def style_prompt(style):
    if not style:
        return ''
    if style not in STYLES:
        raise ValueError('不支持的画面风格，请重新选择')
    return ('画面风格约束：' + STYLES[style]
            + ' 在剧本、角色外貌与服装、场景环境、每条分镜和最终生成提示词中保留此风格。'
            '保持要求的输出结构，不新增JSON字段；与旧文本的美术风格冲突时以本约束为准，保留剧情与人物身份。')


def resolve_styles(nodes, edges, targets=None):
    by_id = {node['id']: node for node in nodes}
    parents = {key: [] for key in by_id}
    for edge in edges:
        if edge.get('data', {}).get('kind') != 'sequence' and edge['source'] in by_id and edge['target'] in by_id:
            parents[edge['target']].append(edge['source'])
    resolved, visiting = {}, set()

    def resolve(key):
        if key in resolved:
            return resolved[key]
        if key in visiting:
            raise ValueError('画面风格继承存在循环连接')
        visiting.add(key)
        explicit = by_id[key]['data'].get('config', {}).get('visualStyle', '')
        if not isinstance(explicit, str) or (explicit and explicit not in STYLES):
            raise ValueError('不支持的画面风格，请重新选择')
        inherited = {resolve(parent) for parent in parents[key]} if not explicit else set()
        inherited.discard('')
        if len(inherited) > 1:
            raise ValueError('上游画面风格不一致，请在节点中明确选择画面风格')
        resolved[key] = explicit or next(iter(inherited), '')
        visiting.remove(key)
        return resolved[key]

    for key in targets if targets is not None else by_id:
        resolve(key)
    return resolved
