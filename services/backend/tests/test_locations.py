import json

import httpx
import pytest

from app.costs import quote_snapshot
from app.generation_profiles import build_workflow_request
from app.providers import TextProvider, ProviderError
from app.store import Store
from test_text_input import setup
from test_full_workflow import profile


def test_location_extraction_and_four_views(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, story='青年走进旧车站。')
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'location.extract'
    store.save_canvas(p['id'], c, c['version'])
    seen = []
    def post(client, url, **kwargs):
        seen.append(kwargs['json'])
        content = json.dumps([{'name': '旧车站', 'description': '雨夜，昏黄灯光', 'layout': '木椅靠东墙，北面入口', 'restrictions': '无现代广告', 'assetId': 'untrusted'}])
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': content}}]})
    monkeypatch.setattr(httpx.Client, 'post', post)
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['status'] == 'completed' and task['submitted'] == 1
    assert seen[0]['messages'][1]['content'] == '青年走进旧车站。'
    location = task['output']['locations'][0]
    assert location['layout'] == '木椅靠东墙，北面入口' and 'assetId' not in location
    assert Store.queue_name(task['snapshot']) == 'text'
    assert quote_snapshot(task['snapshot'], {})['provider'] == 'text'
    task['snapshot']['kind'] = 'image.location'
    config, inputs, key = worker.inputs(task)
    assert '2×2' in config['prompt']
    for view in ['前视图', '右视图', '后视图', '左视图', '青年走进旧车站。']:
        assert view in config['prompt']
    assert worker.inputs(task)[0] == config
    for custom in [None, profile('image.location')]:
        request = build_workflow_request('image.location', config, {'image': [b'ref']}, custom)
        assert any(v['fieldValue'] == config['prompt'] for v in request['user_data'])
        assert any(v['fieldValue'] == b'ref' for v in request['user_data'])
    assert Store.queue_name({'kind': 'image.location'}) == 'media'


@pytest.mark.parametrize('value', [[], [{'name': ''}], [{'name': '车站', 'layout': []}], [{'name': '车站'}, {'name': '车站'}]])
def test_location_invalid_structure_rejected(tmp_path, monkeypatch, value):
    _, _, worker = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(httpx.Client, 'post', lambda client, url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': json.dumps(value)}}]}))
    with pytest.raises(ProviderError):
        TextProvider(worker.settings).generate('location.extract', '车站故事')


def test_empty_location_still_rejected(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, story='  ')
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'image.location'
    store.save_canvas(p['id'], c, c['version'])
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['error_code'] == 'EMPTY_TEXT_INPUT' and task['submitted'] == 0
