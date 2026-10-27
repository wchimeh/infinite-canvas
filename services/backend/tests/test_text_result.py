import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.text_result import edited_result
from app.shot_nodes import SECTIONS
from app.store import Store
from test_text_input import setup


@pytest.mark.parametrize('kind,field,items', [
    ('character.extract', 'characters', [{'name': 'Alice', 'description': 'updated'}]),
    ('location.extract', 'locations', [{'name': 'House', 'layout': 'updated'}]),
    ('shots.extract', 'shots', [{'visualPrompt': 'updated', 'durationMs': 10000}]),
])
def test_structured_edits_are_synchronized(kind, field, items):
    result = edited_result(kind, json.dumps(items), {})
    assert result[field] == json.loads(result['text']) == items


@pytest.mark.parametrize('kind,text', [
    ('script.expand', ' '), ('character.extract', 'plain text'),
    ('character.extract', '[{"name":"a"},{"name":"A"}]'),
    ('shots.extract', '[{"visualPrompt":"x","durationMs":1000}]'),
    ('prompt.video_expand', 'missing sections'), ('image.generate', 'x'),
])
def test_invalid_edit_rejected(kind, text):
    with pytest.raises(ValueError):
        edited_result(kind, text, {})


def test_edits_preserve_style_duration_and_reference_metadata():
    shots = [{'visualPrompt': 'updated', 'durationMs': 10000}]
    result = edited_result('shots.extract', json.dumps(shots), {'shots': [{**shots[0], 'visualStyle': 'live_action'}]})
    assert result['shots'][0]['visualStyle'] == 'live_action'
    assert json.loads(result['text']) == result['shots']
    text = '\n'.join(section + ': N/A' for section in SECTIONS)
    result = edited_result('prompt.video_expand', text, {'seconds': 10, 'referenceImageHashes': ['first', 'second']})
    assert result['seconds'] == 10 and result['referenceImageHashes'] == ['first', 'second']


def test_edited_output_persists_and_feeds_downstream_without_cloud(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    canvas = store.canvas(project['id'])
    canvas['nodes'][1]['data']['config']['editedResult'] = {'text': 'manual version'}
    canvas['nodes'].append({'id': 'concat', 'type': 'studio', 'position': {'x': 600, 'y': 0},
                            'data': {'kind': 'text.concat', 'config': {}}})
    canvas['edges'].append({'id': 'edited', 'source': 'script', 'target': 'concat',
                            'sourceHandle': 'text', 'targetHandle': 'text', 'data': {'kind': 'data'}})
    store.save_canvas(project['id'], canvas, canvas['version'])
    assert Store(tmp_path / 'projects').canvas(project['id'])['nodes'][1]['data']['config']['editedResult']['text'] == 'manual version'
    monkeypatch.setattr(worker.provider, 'submit', lambda *a, **kw: pytest.fail('No cloud'))
    monkeypatch.setattr('app.providers.TextProvider.generate', lambda *a, **kw: pytest.fail('No LLM'))
    for text in ('manual version', 'updated version'):
        canvas = store.canvas(project['id'])
        canvas['nodes'][1]['data']['config']['editedResult']['text'] = text
        store.save_canvas(project['id'], canvas, canvas['version'])
        run = worker.submit(project['id'], ['concat'], force=True)
        worker.tick(); worker.tick()
        tasks = store.run(run['id'])['tasks']
        assert {task['node_id'] for task in tasks} == {'script', 'concat'}
        assert all(task['status'] == 'completed' and task['output']['text'] == text for task in tasks)
        edited = next(task for task in tasks if task['node_id'] == 'script')
        assert edited['input_hash'] is None
        assert edited['snapshot']['quote']['amount'] == '0.000000'
        assert Store.queue_name(edited['snapshot']) == 'local'


def test_preview_preserves_history(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    worker.mock = True
    run = worker.submit(project['id'], ['script'])
    worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    app = create_app(root=tmp_path / 'projects', token='test', start_worker=False, settings=worker.settings)
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost', 'authorization': 'Bearer test'})
        response = client.post(f"/api/v1/tasks/{task['id']}/text-preview", json={'text': 'edited'})
        assert response.status_code == 200, response.text
        assert response.json() == {'text': 'edited'}
        assert store.task(task['id'])['output'] == task['output']
