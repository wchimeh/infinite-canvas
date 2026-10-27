import pytest

from app.visual_style import resolve_styles, style_prompt


def node(key, style=None):
    return {'id': key, 'data': {'config': {} if style is None else {'visualStyle': style}}}


def edge(source, target):
    return {'source': source, 'target': target}


def test_style_inherits_through_entire_chain():
    keys = ['story', 'script', 'characters', 'image', 'shots', 'select', 'expand', 'video']
    nodes = [node(key, 'live_action' if i == 0 else None) for i, key in enumerate(keys)]
    assert set(resolve_styles(nodes, [edge(a, b) for a, b in zip(keys, keys[1:])]).values()) == {'live_action'}


def test_explicit_override_and_conflict():
    nodes = [node('a', 'live_action'), node('b', 'anime'), node('c')]
    edges = [edge('a', 'c'), edge('b', 'c')]
    with pytest.raises(ValueError, match='风格'):
        resolve_styles(nodes, edges)
    nodes[2] = node('c', 'live_action')
    assert resolve_styles(nodes, edges)['c'] == 'live_action'


def test_no_style_and_sequence_do_not_imply_anime():
    assert resolve_styles([node('a'), node('b')], [edge('a', 'b')]) == {'a': '', 'b': ''}
    assert resolve_styles([node('a', 'anime'), node('b')], [{**edge('a', 'b'), 'data': {'kind': 'sequence'}}])['b'] == ''
    assert style_prompt('') == ''


def test_live_action_constraints_and_invalid_value():
    assert '真人实拍' in style_prompt('live_action')
    assert '不要动漫' in style_prompt('live_action')
    with pytest.raises(ValueError):
        resolve_styles([node('a', 'invalid')], [])


@pytest.mark.parametrize('kind', ['script.expand', 'character.extract', 'location.extract',
                                'shots.extract', 'prompt.video_expand', 'image.character',
                                'image.location', 'image.generate', 'video.image_to_video'])
def test_worker_request_inherits_style_and_invalidates_cache(tmp_path, kind):
    from app.credentials import Settings
    from app.store import Store
    from app.worker import Worker

    store = Store(tmp_path / 'data')
    pid = store.create_project('style')['id']
    worker = Worker(store, mock=True, settings=Settings(tmp_path / 'settings'))
    canvas = store.canvas(pid)
    canvas['nodes'] = [
        {'id': 'source', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'story.prompt', 'config': {'prompt': 'A visitor arrives.', 'visualStyle': 'live_action'}}},
        {'id': 'target', 'position': {'x': 300, 'y': 0}, 'data': {'kind': kind, 'config': {}}},
    ]
    canvas['edges'] = [{'id': 'link', 'source': 'source', 'target': 'target', 'sourceHandle': 'text', 'targetHandle': 'text', 'data': {'kind': 'data'}}]
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['target'])
    tasks = store.run(run['id'])['tasks']
    task = next(task for task in tasks if task['node_id'] == 'target')
    dependencies = {'source': {'output': {'text': 'A visitor arrives.'}}}
    config, _, key = worker.inputs(task, dependency_outputs=dependencies)
    assert config['visualStyle'] == 'live_action'
    assert '真人实拍' in config['prompt'] and '不要动漫' in config['prompt']
    if kind.startswith(('image.', 'video.')):
        from app.generation_profiles import build_workflow_request
        # Pure request assembly: the video workflow needs a reference input;
        # no file upload, provider call or paid generation is performed.
        media = {'image': [b'reference-fixture']} if kind.startswith('video.') else {}
        request = build_workflow_request(kind, config, media, config.get('_workflow'))
        values = [entry.get('fieldValue') for entry in request.get('nodeInfoList', []) + request.get('user_data', [])]
        assert any(isinstance(value, str) and '真人实拍' in value and '不要动漫' in value for value in values)
    task['snapshot']['config']['visualStyle'] = 'anime'
    other, _, other_key = worker.inputs(task, dependency_outputs=dependencies)
    assert key != other_key and '二维动漫' in other['prompt']
    source = next(task for task in tasks if task['node_id'] == 'source')
    source_config, _, _ = worker.inputs(source, dependency_outputs={})
    assert source_config['prompt'] == 'A visitor arrives.'
    assert 'visualStyle' not in store.canvas(pid)['nodes'][1]['data']['config']


def test_unrelated_conflicting_branch_does_not_block_selection():
    nodes = [node('a', 'anime'), node('b', 'live_action'), node('c'), node('d')]
    result = resolve_styles(nodes, [edge('a', 'c'), edge('b', 'c')], ['d'])
    assert result == {'d': ''}
