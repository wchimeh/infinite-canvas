import pytest

from test_review_fixes import setup_project


def prepare(tmp_path):
    store, project, worker = setup_project(tmp_path, kind='image.character')
    original = worker.submit(project['id']); worker.tick()
    completed = store.run(original['id'])['tasks'][0]
    canvas = store.canvas(project['id'])
    canvas['nodes'].append({'id': 'downstream', 'type': 'studio', 'position': {'x': 300, 'y': 0},
                            'data': {'kind': 'image.generate', 'config': {'prompt': 'use reference'}}})
    canvas['edges'].append({'id': 'link', 'source': 'node', 'target': 'downstream',
                           'sourceHandle': 'image', 'targetHandle': 'image', 'data': {'kind': 'data'}})
    store.save_canvas(project['id'], canvas, canvas['version'])
    return store, project, worker, completed


def test_cached_upstream_completed_at_submission(tmp_path):
    store, project, worker, completed = prepare(tmp_path)
    estimate = worker.submit(project['id'], ['downstream'], dry_run=True)
    assert estimate['quotes'][0]['basis'] == 'cache'
    assert estimate['quotes'][0]['amount'] == '0.000000'
    run = worker.submit(project['id'], ['downstream'])
    tasks = store.run(run['id'])['tasks']
    upstream = next(t for t in tasks if t['node_id'] == 'node')
    downstream = next(t for t in tasks if t['node_id'] == 'downstream')
    assert upstream['status'] == 'completed' and upstream['reused'] == 1
    assert upstream['submitted'] == 0 and upstream['external_id'] is None
    assert upstream['output'] == completed['output']
    assert upstream['input_hash'] == completed['input_hash']
    assert worker.inputs(downstream)[1]['image']


@pytest.mark.parametrize('invalidate', ['prompt', 'deleted', 'force'])
def test_changed_or_forced_upstream_queued(tmp_path, invalidate):
    store, project, worker, completed = prepare(tmp_path)
    if invalidate == 'prompt':
        canvas = store.canvas(project['id'])
        canvas['nodes'][0]['data']['config']['prompt'] = 'changed'
        store.save_canvas(project['id'], canvas, canvas['version'])
    elif invalidate == 'deleted':
        store.delete_asset(completed['output']['assets'][0])
    selected = ['node', 'downstream'] if invalidate == 'force' else ['downstream']
    run = worker.submit(project['id'], selected, force=invalidate == 'force')
    upstream = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'node')
    assert upstream['status'] == 'queued' and upstream['reused'] == 0
