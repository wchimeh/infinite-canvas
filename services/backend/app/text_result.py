"""人工采用的文本输出，不修改生成历史或生成缓存。"""
import copy
import json

from app.shot_nodes import validate_expansion, validate_timing_budget

EDITABLE_KINDS = {'script.expand', 'prompt.video_expand', 'character.extract',
                  'location.extract', 'shots.extract', 'text.concat'}


def edited_result(kind, text, original):
    if kind not in EDITABLE_KINDS:
        raise ValueError('此节点不支持编辑生成结果')
    if not isinstance(text, str) or not text.strip() or len(text) > 200000:
        raise ValueError('文本不能为空，且不能超过 200000 字符')
    output = {'text': text}
    if kind == 'prompt.video_expand':
        seconds = original.get('seconds', 5)
        if type(seconds) not in (int, float) or not 4 <= seconds <= 15:
            raise ValueError('原结果时长无效，请重新扩写')
        output.update(text=validate_expansion(text), seconds=seconds)
        validate_timing_budget(text, seconds)
        if 'referenceImageHashes' in original:
            output['referenceImageHashes'] = copy.deepcopy(original['referenceImageHashes'])
    if kind in ('character.extract', 'location.extract', 'shots.extract'):
        try:
            items = json.loads(text)
        except ValueError as exc:
            raise ValueError('请输入有效的 JSON 数组，保留双引号和字段名') from exc
        shots = kind == 'shots.extract'
        if not isinstance(items, list) or not 1 <= len(items) <= (50 if shots else 20):
            raise ValueError('分镜需包含 1–50 项，角色或场景需包含 1–20 项')
        names = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError('每一项必须是 JSON 对象')
            if shots:
                if (not isinstance(item.get('visualPrompt'), str) or not item['visualPrompt'].strip()
                        or type(item.get('durationMs')) is not int or not 4000 <= item['durationMs'] <= 15000):
                    raise ValueError('每个分镜需要 visualPrompt，durationMs 必须是 4000–15000 的整数')
                fields = ('title', 'dialogue', 'shotSize', 'cameraMove')
                originals = original.get('shots', [])
                if isinstance(originals, list) and index < len(originals) and isinstance(originals[index], dict) and originals[index].get('visualStyle'):
                    item.setdefault('visualStyle', originals[index]['visualStyle'])
            else:
                fields = ('name', 'description', 'layout', 'restrictions') if kind == 'location.extract' else ('name', 'description', 'appearance', 'wardrobe', 'restrictions')
                name = item.get('name')
                if not isinstance(name, str) or not name.strip() or name.strip().casefold() in names or len(name) > 100:
                    raise ValueError('名称必须非空、唯一，且不超过 100 字符')
                names.add(name.strip().casefold())
            if any(not isinstance(item.get(field, ''), str) or len(item.get(field, '')) > 4000 for field in fields):
                raise ValueError('描述字段必须为文本，且不超过 4000 字符')
        output['shots' if shots else 'characters' if kind == 'character.extract' else 'locations'] = items
        output['text'] = json.dumps(items, ensure_ascii=False, indent=2)
    return output
