import json

import httpx
import pytest

from app.costs import quote_snapshot
from app.graph import DEFINITIONS
from app.generation_profiles import build_workflow_request, resolve_selection
from app.providers import ProviderError, TextProvider
from app.store import Store
from test_text_input import setup
from test_full_workflow import profile


def test_character_extraction_uses_real_text_adapter(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch)
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'character.extract'
    store.save_canvas(p['id'], c, c['version'])
    seen = []
    def post(client, url, **kwargs):
        seen.append(kwargs['json'])
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': '```json\n' + json.dumps([{'name': ' 小林 ', 'description': '年轻创业者', 'appearance': '短发', 'wardrobe': '白衬衫', 'assetId': 'untrusted'}]) + '\n```'}}]})
    monkeypatch.setattr(httpx.Client, 'post', post)
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['status'] == 'completed' and task['submitted'] == 1
    assert seen[0]['messages'][1]['content'] == '一个年轻小伙赚大钱的故事'
    assert '提取主要角色' in seen[0]['messages'][0]['content']
    assert task['output']['characters'][0] == {'name': '小林', 'description': '年轻创业者', 'appearance': '短发', 'wardrobe': '白衬衫', 'restrictions': ''}
    assert Store.queue_name(task['snapshot']) == 'text'
    assert quote_snapshot(task['snapshot'], {})['provider'] == 'text'


@pytest.mark.parametrize('value', [[], {'name': 'x'}, [{'name': ''}], [{'name': 'x', 'appearance': []}], [{'name': 'x'}, {'name': 'X'}], [{'name': str(i)} for i in range(21)]])
def test_invalid_character_response_rejected(tmp_path, monkeypatch, value):
    _, _, worker = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(httpx.Client, 'post', lambda client, url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': json.dumps(value)}}]}))
    with pytest.raises(ProviderError, match='格式'):
        TextProvider(worker.settings).generate('character.extract', '一段故事')


def test_character_image_workflows_and_queue():
    assert DEFINITIONS['image.character']['outputs'] == {'image': 'image'}
    assert Store.queue_name({'kind': 'image.character'}) == 'media'
    request = build_workflow_request('image.character', {'prompt': '短发白衣'}, {'image': [b'reference']})
    assert any(v['fieldValue'] == '短发白衣' for v in request['user_data'])
    assert any(v['fieldValue'] == b'reference' for v in request['user_data'])
    request = build_workflow_request('image.character', {'prompt': '角色图'}, {'image': [b'reference']}, profile('image.character'))
    assert any(v['fieldValue'] == '角色图' for v in request['user_data'])
    selection = resolve_selection({'textServices': [{'id': 'custom', 'enabled': True, 'models': ['role-model'], 'defaultModel': 'role-model', 'baseUrl': 'https://text.invalid'}]}, 'character.extract', {'textServiceId': 'custom'})
    assert selection['textModel'] == 'role-model' and selection['textCredential'] == 'text-custom'


def test_character_extraction_respects_cloud_switch(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch)
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'character.extract'
    store.save_canvas(p['id'], c, c['version'])
    p['settings']['cloudEnabled'] = False; store.put_document(p['id'], 'project', p)
    with pytest.raises(ValueError, match='云端'):
        worker.submit(p['id'], ['script'])


def test_character_three_views_prompt_and_cache(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, extra='白色衬衫')
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'image.character'
    store.save_canvas(p['id'], c, c['version'])
    run = worker.submit(p['id'], ['script']); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    config, inputs, key = worker.inputs(task)
    for text in ['正面', '侧面', '背面', '同一张', '白色衬衫', '一个年轻小伙赚大钱的故事']:
        assert text in config['prompt']
    assert worker.inputs(task)[0]['prompt'] == config['prompt']
    assert task['snapshot']['config']['prompt'] == '白色衬衫'
    request = build_workflow_request('image.character', config, inputs)
    assert any(value['fieldValue'] == config['prompt'] for value in request['user_data'])
    custom = profile('image.character'); custom['mappings'] = custom['mappings'][:1]
    assert build_workflow_request('image.character', config, inputs, custom)['user_data'][0]['fieldValue'] == config['prompt']
    from app.graph import snapshot_hash
    old_config = {**config, 'prompt': '一个年轻小伙赚大钱的故事\n\n白色衬衫'}
    assert snapshot_hash(old_config) != snapshot_hash(config)
    task['snapshot']['kind'] = 'image.generate'
    ordinary, _, _ = worker.inputs(task)
    assert ordinary['prompt'] == old_config['prompt']


def test_empty_character_prompt_stays_empty(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, story=' ')
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'image.character'
    store.save_canvas(p['id'], c, c['version'])
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['error_code'] == 'EMPTY_TEXT_INPUT' and task['submitted'] == 0


@pytest.mark.parametrize('kind,field', [('image.character', 'characters'), ('image.location', 'locations')])
def test_multiple_subjects_rejected_before_cache_or_submission(tmp_path, monkeypatch, kind, field):
    store, p, worker = setup(tmp_path, monkeypatch)
    canvas = store.canvas(p['id']); canvas['nodes'][1]['data']['kind'] = kind
    store.save_canvas(p['id'], canvas, canvas['version'])
    run = worker.submit(p['id'], ['script']); worker.tick()
    upstream = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'story')
    store.update_task(upstream['id'], output={'text': 'two subjects', field: [{'name': 'A'}, {'name': 'B'}]})
    calls = []
    monkeypatch.setattr(store, 'cached', lambda *args: calls.append('cache'))
    monkeypatch.setattr(httpx.Client, 'post', lambda *args, **kwargs: calls.append('http'))
    worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['status'] == 'failed' and task['error_code'] == 'MULTIPLE_SUBJECTS'
    assert task['submitted'] == 0 and calls == []


@pytest.mark.parametrize('kind,field', [('image.character', 'characters'), ('image.location', 'locations')])
def test_single_subject_and_existing_remote_job_inputs_allowed(tmp_path, monkeypatch, kind, field):
    store, p, worker = setup(tmp_path, monkeypatch)
    canvas = store.canvas(p['id']); canvas['nodes'][1]['data']['kind'] = kind
    store.save_canvas(p['id'], canvas, canvas['version'])
    run = worker.submit(p['id'], ['script']); worker.tick()
    tasks = store.run(run['id'])['tasks']
    upstream = next(t for t in tasks if t['node_id'] == 'story')
    task = next(t for t in tasks if t['node_id'] == 'script')
    store.update_task(upstream['id'], output={'text': 'subject A', field: [{'name': 'A'}]})
    assert 'subject A' in worker.inputs(task)[0]['prompt']
    store.update_task(upstream['id'], output={'text': 'existing remote job', field: [{'name': 'A'}, {'name': 'B'}]})
    task['external_id'] = 'already-submitted'
    assert 'existing remote job' in worker.inputs(task)[0]['prompt']
