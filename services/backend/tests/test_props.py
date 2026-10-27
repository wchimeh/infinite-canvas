import io

import pytest
from PIL import Image

from app.generation_profiles import build_workflow_request, resolve_selection, validate_workflow
from app.store import Store
from test_full_workflow import profile
from test_text_input import setup


@pytest.mark.parametrize('story,extra,count', [('铜制怀表', '', 0), ('', '木箱', 0), ('铜制怀表', '保持刻纹', 2), ('', '', 1), ('', '', 8)])
def test_prop_four_views_and_references(tmp_path, monkeypatch, story, extra, count):
    store, project, worker = setup(tmp_path, monkeypatch, story=story, extra=extra)
    pid = project['id']
    canvas = store.canvas(pid)
    refs, bodies = [], []
    for index in range(count):
        buffer = io.BytesIO()
        Image.new('RGB', (16, 16), (index * 30, 0, 0)).save(buffer, 'PNG')
        bodies.append(buffer.getvalue())
        refs.append(store.add_asset(pid, bodies[-1], f'ref{index}.png')['id'])
    canvas['nodes'][0]['data']['config']['visualStyle'] = 'live_action'
    canvas['nodes'][1]['data']['kind'] = 'image.prop'
    canvas['nodes'][1]['data']['config'].update(referenceIds=refs, workflowId='builtin-image2')
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    config, inputs, key = worker.inputs(task)
    assert all(word in config['prompt'] for word in ['道具', '2×2', '前视图', '右视图', '后视图', '左视图', '真人实拍'])
    assert story in config['prompt'] and extra in config['prompt']
    assert inputs.get('image', []) == bodies
    assert worker.inputs(task) == (config, inputs, key)
    assert Store.queue_name(task['snapshot']) == 'media'
    builtin = resolve_selection({}, 'image.prop', {'workflowId': 'builtin-image2'})['cloudWorkflow']
    for workflow in [None, builtin]:
        request = build_workflow_request('image.prop', config, inputs, workflow)
        assert any(v['fieldValue'] == config['prompt'] for v in request['user_data'])
        assert [v['fieldValue'] for v in request['user_data'] if isinstance(v['fieldValue'], bytes)] == bodies
    custom = profile('image.prop')
    validate_workflow(custom)
    request = build_workflow_request('image.prop', config, {'image': [b'reference']}, custom)
    assert any(v['fieldValue'] == b'reference' for v in request['user_data'])
    assert any(v['fieldValue'] == config['prompt'] for v in request['user_data'])


def test_empty_prop_does_not_submit(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch, story='  ')
    canvas = store.canvas(project['id'])
    canvas['nodes'][1]['data'].update(kind='image.prop', config={'visualStyle': 'live_action'})
    store.save_canvas(project['id'], canvas, canvas['version'])
    run = worker.submit(project['id'], ['script'])
    worker.tick()
    worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['error_code'] == 'EMPTY_TEXT_INPUT' and task['submitted'] == 0


def test_prop_rejects_too_many_builtin_references():
    with pytest.raises(ValueError, match='8'):
        build_workflow_request('image.prop', {'prompt': '木箱'}, {'image': [b'ref'] * 9})
