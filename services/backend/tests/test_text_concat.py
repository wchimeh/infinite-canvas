import pytest

from app.costs import quote_snapshot
from app.credentials import Settings
from app.graph import validate_graph
from app.store import Store
from app.worker import Worker


def node(id, kind, config):
    return {'id': id, 'type': 'studio', 'position': {'x': 0, 'y': 0},
            'data': {'kind': kind, 'config': config}}


def setup(tmp_path, separator):
    store = Store(tmp_path / 'data')
    project = store.create_project('Concatenation')
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [node('first', 'story.prompt', {'prompt': ' A '}),
                       node('empty', 'story.prompt', {'prompt': ''}),
                       node('last', 'story.prompt', {'prompt': 'B\n'}),
                       node('concat', 'text.concat', {} if separator is None else {'separator': separator})]
    canvas['edges'] = [{'id': source, 'source': source, 'target': 'concat', 'sourceHandle': 'text',
                        'targetHandle': port, 'data': {'kind': 'data'}}
                       for source, port in [('last', 'text10'), ('empty', 'text2'), ('first', 'text')]]
    return store, project, worker, canvas


def execute(store, project, worker):
    run = worker.submit(project['id'], ['concat'])
    for _ in range(8):
        if not worker.tick():
            break
    tasks = store.run(run['id'])['tasks']
    assert all(task['status'] == 'completed' for task in tasks)
    return next(task for task in tasks if task['node_id'] == 'concat')


@pytest.mark.parametrize('separator', [None, '', ' ', '\n', ' | ', '\\n'])
def test_concat_is_local_ordered_and_preserves_empty_text(tmp_path, monkeypatch, separator):
    store, project, worker, canvas = setup(tmp_path, separator)
    monkeypatch.setattr(worker.provider, 'submit', lambda *a, **kw: pytest.fail('Cloud must not be called'))
    store.save_canvas(project['id'], canvas, canvas['version'])
    task = execute(store, project, worker)
    assert task['output'] == {'text': ('\n' if separator is None else separator).join([' A ', '', 'B\n'])}
    assert Store.queue_name(task['snapshot']) == 'local'
    assert task['snapshot']['quote']['amount'] == '0.000000'
    assert not task['external_id']
    cached = execute(store, project, worker)
    assert cached['reused']
    canvas = store.canvas(project['id'])
    canvas['nodes'][-1]['data']['config']['separator'] = 'changed'
    store.save_canvas(project['id'], canvas, canvas['version'])
    changed = execute(store, project, worker)
    assert changed['output']['text'] == 'changed'.join([' A ', '', 'B\n'])
    assert changed['input_hash'] != task['input_hash']


def test_concat_without_connections_is_empty(tmp_path):
    store, project, worker, canvas = setup(tmp_path, None)
    canvas['edges'] = []
    store.save_canvas(project['id'], canvas, canvas['version'])
    assert execute(store, project, worker)['output'] == {'text': ''}


def test_concat_validation_and_price():
    assert not validate_graph([node('a', 'text.concat', {'separator': ''})], [])['errors']
    assert validate_graph([node('a', 'text.concat', {'separator': 123})], [])['errors']
    quote = quote_snapshot({'kind': 'text.concat', 'config': {}}, {})
    assert quote['basis'] == 'local' and quote['amount'] == '0.000000'
