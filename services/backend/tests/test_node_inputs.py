import copy
import json
from unittest.mock import Mock

import httpx
import pytest

from app.comfy import ComfyUI
from app.generation_profiles import build_workflow_request
from app.providers import ProviderError, RunningHub, TextProvider
from app.worker import Worker
from generate_tool.rh_generate_workflow import build_request
from test_text_input import setup
from test_comfy import workflow, transport


@pytest.mark.parametrize('kind,port', [('image.generate', 'image'), ('image.variation', 'image'),
    ('video.image_to_video', 'image'), ('audio.tts', 'audio'), ('video.sound_effects', 'video')])
@pytest.mark.parametrize('full', [False, True])
def test_upstream_to_cloud_http(tmp_path, kind, port, full):
    path = tmp_path / 'asset'; path.write_bytes(b'upstream-media')
    store = Mock()
    store.task.side_effect = lambda id: {'node_id': id, 'output': {'text': '上游内容'} if id == 'story' else {'assets': ['asset']}}
    store.asset_path.return_value = path
    store.asset.return_value = {'mime': port + '/fixture', 'sha256': 'hash'}
    worker = Worker(store)
    snap = {'kind': kind, 'config': {'prompt': '补充要求', 'voiceAuthorized': True}, 'references': [],
            'links': [{'source': 'story', 'port': 'text'}, {'source': 'media', 'port': port}],
            'adapterVersion': 'qa', 'textModel': '', 'textEndpoint': ''}
    config, inputs, _ = worker.inputs({'snapshot': snap, 'deps': ['story', 'media']})
    assert config['prompt'] == '上游内容\n\n补充要求'
    assert inputs == {port: [b'upstream-media']}
    if full:
        config['_workflow'] = {'id': 'qa', 'name': 'QA', 'version': 1, 'enabled': True, 'kinds': [kind],
            'workflow': {'1': {'class_type': 'QA', 'inputs': {'text': '', 'file': ''}}},
            'mappings': [{'source': 'prompt', 'nodeId': '1', 'fieldName': 'text'}, {'source': port, 'nodeId': '1', 'fieldName': 'file'}], 'resultNodes': ['1']}
    seen = []
    def handle(request):
        if request.url.path.endswith('/upload'):
            assert b'upstream-media' in request.content
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'uploaded-file'}})
        body = json.loads(request.content); seen.append(body)
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'qa-task'}})
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit(kind, config, inputs) == 'qa-task'
    values = list(json.loads(seen[0]['workflow'])['1']['inputs'].values()) if full else [v['fieldValue'] for v in seen[0]['nodeInfoList']]
    assert config['prompt'] in values
    assert 'uploaded-file' in values


def test_custom_workflow_cannot_silently_ignore_text():
    profile = {'id': 'qa', 'name': 'QA', 'version': 1, 'enabled': True, 'kinds': ['image.generate'],
               'workflow': {'1': {'class_type': 'QA', 'inputs': {'text': 'fixed'}}}, 'mappings': [], 'resultNodes': ['1']}
    with pytest.raises(ValueError, match='提示词'):
        build_workflow_request('image.generate', {'prompt': '上游内容'}, {}, profile)
    assert build_workflow_request('image.generate', {}, {}, profile)['workflow']['1']['inputs']['text'] == 'fixed'


@pytest.mark.parametrize('field,config,inputs', [('prompt', {'prompt': '上游内容'}, {}), ('image', {}, {'image': [b'image']})])
def test_comfy_unmapped_input_rejected_before_upload(field, config, inputs):
    definitions = workflow(); definitions['image.generate']['mappings'] = {}
    seen = []
    provider = ComfyUI('http://localhost:8188', definitions, httpx.Client(transport=transport(seen)))
    with pytest.raises(ProviderError, match='映射'):
        provider.submit('image.generate', config, inputs)
    assert not any(r.method == 'POST' for r in seen)


def test_builtin_voice_rejects_extra_references():
    with pytest.raises(ValueError, match='1'):
        build_request('audio.tts', {'prompt': '你好', 'voiceAuthorized': True}, {'audio': [b'one', b'two']})


def test_empty_upstream_image_does_not_submit(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, story='   ')
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'image.generate'
    store.save_canvas(p['id'], c, c['version'])
    calls = []
    monkeypatch.setattr(worker.provider, 'submit', lambda *args: calls.append(args) or 'qa')
    monkeypatch.setattr(worker.provider, 'poll', lambda *args: 'QUEUED')
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert calls == []
    assert task['error_code'] == 'EMPTY_TEXT_INPUT'
    assert task['submitted'] == 0


def test_shots_uses_upstream_and_short_outline_instruction(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch)
    c = store.canvas(p['id']); c['nodes'][1]['data']['kind'] = 'shots.extract'
    store.save_canvas(p['id'], c, c['version'])
    calls = []
    def post(client, url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': json.dumps([{'visualPrompt': '年轻人创业', 'dialogue': '', 'durationMs': 5000}])}}]})
    monkeypatch.setattr(httpx.Client, 'post', post)
    run = worker.submit(p['id'], ['script']); worker.tick(); worker.tick()
    assert calls[0]['messages'][1]['content'] == '一个年轻小伙赚大钱的故事'
    assert '梗概' in calls[0]['messages'][0]['content']
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert task['status'] == 'completed' and task['output']['shots']
