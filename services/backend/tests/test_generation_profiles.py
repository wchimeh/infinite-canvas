import copy
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.credentials import Settings
from app.costs import quote_snapshot
from app.providers import RunningHub, TextProvider, ProviderError
from app.store import Store
from app.worker import Worker


class Vault:
    available = True
    def __init__(self):
        self.values = {}
    def get(self, name):
        return self.values.get(name, '')
    def set(self, name, value):
        self.values[name] = value
    def delete(self, name):
        self.values.pop(name, None)


def service(id='alpha', **changes):
    return {'id': id, 'name': id, 'baseUrl': f'https://{id}.example/v1',
            'models': ['small', 'large'], 'defaultModel': 'small', 'enabled': True, **changes}


def workflow(id='portrait', **changes):
    return {'id': id, 'name': id, 'kinds': ['image.generate', 'image.variation'], 'version': 1, 'enabled': True,
            'workflowId': '123', 'nodeInfoList': [{'nodeId': '1', 'fieldName': 'steps', 'fieldValue': 20}],
            'mappings': [{'source': 'prompt', 'nodeId': '2', 'fieldName': 'text'},
                         {'source': 'image', 'nodeId': '3', 'fieldName': 'reference', 'index': 0, 'required': False}],
            'resultNodes': ['9'], **changes}


@pytest.fixture
def settings(tmp_path, monkeypatch):
    for key in ('TEXT_API_KEY', 'TEXT_API_BASE', 'TEXT_MODEL', 'RUNNINGHUB_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    return Settings(tmp_path / 'settings', Vault())


def test_profiles_persist_and_keys_are_isolated(settings, monkeypatch):
    settings.save({'textServices': [service(), service('beta')], 'cloudWorkflows': [workflow()]})
    settings.set_key('text-alpha', 'alpha-secret')
    settings.set_key('text-beta', 'beta-secret')
    monkeypatch.setenv('TEXT_API_KEY', 'legacy-secret')
    assert settings.key('text-alpha') == 'alpha-secret'
    assert settings.key('text-beta') == 'beta-secret'
    assert settings.key('text') == 'legacy-secret'
    public = settings.public()
    assert public['credentials']['text-alpha']['configured']
    assert 'alpha-secret' not in json.dumps(public)
    assert 'beta-secret' not in settings.path.read_text()
    reopened = Settings(settings.root, settings.vault)
    assert reopened.load()['textServices'][1]['models'] == ['small', 'large']
    settings.delete_key('text-alpha')
    assert settings.key('text-alpha') == ''
    assert settings.key('text-beta') == 'beta-secret'


@pytest.mark.parametrize('changes', [
    {'textServices': [service(), service()]},
    {'textServices': [service(baseUrl='file:///bad')]},
    {'textServices': [service(defaultModel='missing')]},
    {'textServices': [service(apiKey='secret')]},
    {'cloudWorkflows': [workflow(resultNodes=[])]},
    {'cloudWorkflows': [workflow(mappings=[{'source': 'unknown', 'nodeId': '2', 'fieldName': 'x'}])]},
    {'cloudWorkflows': [workflow(mappings=[{'source': 'prompt', 'nodeId': '1', 'fieldName': 'steps'}])]},
    {'cloudWorkflows': [workflow(kinds=['script.expand'])]},
])
def test_reject_invalid_profiles(settings, changes):
    with pytest.raises(ValueError):
        settings.save(changes)


def test_resolve_selection_and_build_mapping():
    from app.generation_profiles import resolve_selection, build_workflow_request
    config = {'textServices': [service()], 'cloudWorkflows': [workflow()]}
    resolved = resolve_selection(config, 'script.expand', {'textServiceId': 'alpha', 'textModel': 'large'})
    assert resolved['textEndpoint'] == 'https://alpha.example/v1'
    assert resolved['textCredential'] == 'text-alpha'
    assert resolved['textModel'] == 'large'
    selected = resolve_selection(config, 'image.generate', {'workflowId': 'portrait'})['cloudWorkflow']
    request = build_workflow_request('image.generate', {'prompt': 'hello'}, {'image': [b'image']}, selected)
    assert request['workflowId'] == '123' and request['result_node'] == ['9']
    assert request['user_data'][0]['fieldValue'] == 'hello'
    assert request['user_data'][1]['fieldValue'] == b'image'
    assert config['cloudWorkflows'][0] == workflow()
    for kind, node in [('script.expand', {'textServiceId': 'alpha', 'textModel': 'missing'}),
                       ('image.generate', {'workflowId': 'missing'}),
                       ('video.image_to_video', {'workflowId': 'portrait'})]:
        with pytest.raises(ValueError):
            resolve_selection(config, kind, node)
    config['textServices'][0]['enabled'] = False
    with pytest.raises(ValueError):
        resolve_selection(config, 'script.expand', {'textServiceId': 'alpha'})


def test_mapping_missing_and_extra_media_rejected_before_upload():
    from app.generation_profiles import build_workflow_request
    template = workflow()
    template['mappings'][1]['required'] = True
    with pytest.raises(ValueError):
        build_workflow_request('image.generate', {'prompt': 'x'}, {}, template)
    with pytest.raises(ValueError):
        build_workflow_request('image.generate', {'prompt': 'x'}, {'image': [b'a', b'b']}, template)


def test_runninghub_custom_upload_submit_and_output_filter(settings):
    calls = []
    def handler(request):
        calls.append(request)
        endpoint = request.url.path.rsplit('/', 1)[-1]
        if endpoint == 'upload':
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'uploaded.png'}})
        if endpoint == 'create':
            payload = json.loads(request.content)
            assert payload['workflowId'] == '123'
            assert {'nodeId': '3', 'fieldName': 'reference', 'fieldValue': 'uploaded.png'} in payload['nodeInfoList']
            assert not any('_mediaType' in item for item in payload['nodeInfoList'])
            return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'remote'}})
        if endpoint == 'outputs':
            return httpx.Response(200, json={'code': 0, 'data': [
                {'nodeId': 'wrong', 'fileUrl': 'https://www.runninghub.cn/wrong.png', 'fileType': 'png'},
                {'nodeId': '9', 'fileUrl': 'https://www.runninghub.cn/right.png', 'fileType': 'png'}]})
        assert endpoint == 'right.png'
        return httpx.Response(200, content=b'output')
    provider = RunningHub(key='fake', client=httpx.Client(transport=httpx.MockTransport(handler)), settings=settings)
    config = {'prompt': 'hello', '_workflow': workflow()}
    assert provider.submit('image.generate', config, {'image': [b'image']}) == 'remote'
    assert provider.fetch('remote', 'image.generate', config, {'image': [b'image']}) == [(b'output', 'remote.png')]
    assert len(calls) == 4


def test_text_provider_uses_selected_credentials(settings, monkeypatch):
    settings.save({'textServices': [service(), service('beta')]})
    settings.set_key('text-alpha', 'alpha-secret')
    settings.set_key('text-beta', 'beta-secret')
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={'choices': [{'message': {'content': 'result'}}]})
    real_client = httpx.Client
    monkeypatch.setattr('app.providers.httpx.Client', lambda **kw: real_client(transport=httpx.MockTransport(handler)))
    text = TextProvider(settings, 'https://beta.example/v1', 'large', credential='text-beta')
    assert text.generate('script.expand', 'hello')['text'] == 'result'
    assert str(requests[0].url) == 'https://beta.example/v1/chat/completions'
    assert requests[0].headers['authorization'] == 'Bearer beta-secret'
    assert json.loads(requests[0].content)['model'] == 'large'
    settings.delete_key('text-beta')
    with pytest.raises(ProviderError):
        text.generate('script.expand', 'hello')
    assert len(requests) == 1


def make_task(tmp_path, settings, kind, config):
    store = Store(tmp_path / 'projects')
    project = store.create_project('Profiles')
    project['settings']['cloudEnabled'] = True
    store.put_document(project['id'], 'project', project)
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [{'id': 'node', 'position': {'x': 0, 'y': 0}, 'data': {'kind': kind, 'config': {'prompt': 'hello', **config}}}]
    store.save_canvas(project['id'], canvas, canvas['version'])
    worker = Worker(store, mock=True, settings=settings)
    worker.submit(project['id'])
    return store, project, worker, store.tasks(project['id'])[0]


def test_worker_freezes_workflow_and_cache_identity(tmp_path, settings):
    settings.save({'cloudWorkflows': [workflow()]})
    store, project, worker, task = make_task(tmp_path, settings, 'image.generate', {'workflowId': 'portrait'})
    assert task['snapshot']['cloudWorkflow']['workflowId'] == '123'
    first_key = worker.inputs(task)[2]
    settings.save({'cloudWorkflows': [workflow(workflowId='456', version=2)]})
    worker.tick()
    worker.submit(project['id'])
    second = next(t for t in store.tasks(project['id']) if t['id'] != task['id'])
    assert worker.inputs(task)[0]['_workflow']['workflowId'] == '123'
    assert worker.inputs(second)[0]['_workflow']['workflowId'] == '456'
    assert first_key != worker.inputs(second)[2]


def test_worker_freezes_text_service_and_model(tmp_path, settings, monkeypatch):
    settings.save({'textServices': [service(), service('beta')]})
    store, project, worker, task = make_task(tmp_path, settings, 'script.expand', {'textServiceId': 'beta', 'textModel': 'large'})
    settings.set_key('text-beta', 'fake')
    settings.save({'textServices': [service(), service('beta', baseUrl='https://changed.example/v1', enabled=False)]})
    observed = []
    def generate(self, *args):
        observed.append((self.base, self.model, self.credential))
        return {'text': 'done'}
    monkeypatch.setattr(TextProvider, 'generate', generate)
    worker.mock = False
    worker.tick()
    assert observed == [('https://beta.example/v1', 'large', 'text-beta')]
    assert store.task(task['id'])['status'] == 'completed'


def test_pricing_is_scoped_to_selected_profile():
    rule = {'amount': '0.4', 'unit': 'task', 'currency': 'CNY'}
    text = {'kind': 'script.expand', 'config': {}, 'textServiceId': 'alpha', 'textModel': 'large'}
    prices = {'text/alpha/large': rule, 'text/large': rule, 'image.generate': rule}
    assert quote_snapshot(text, prices)['amount'] == '0.400000'
    assert not quote_snapshot({**text, 'textServiceId': 'beta'}, prices)['known']
    image = {'kind': 'image.generate', 'config': {}, 'cloudWorkflow': workflow()}
    assert not quote_snapshot(image, prices)['known']
    assert quote_snapshot(image, {'workflow/portrait': rule})['amount'] == '0.400000'


def test_catalog_api_and_validation(settings, tmp_path):
    from app.main import create_app
    with TestClient(create_app(tmp_path / 'projects', 'test-token', start_worker=False, settings=settings)) as client:
        assert client.get('/api/v1/generation-options').status_code == 401
        client.headers['Authorization'] = 'Bearer test-token'
        assert client.put('/api/v1/settings', json={'textServices': [service()], 'cloudWorkflows': [workflow()]}).status_code == 200
        assert client.put('/api/v1/settings/credentials/text-alpha', json={'key': 'private-value'}).status_code == 200
        result = client.get('/api/v1/generation-options')
        assert result.status_code == 200
        assert 'private-value' not in result.text
        assert any(w['id'] == 'portrait' for w in result.json()['workflows'])
        assert any(s['id'] == 'alpha' and s['ready'] for s in result.json()['textServices'])
        assert client.put('/api/v1/settings', json={'textServices': [service(defaultModel='bad')]}).status_code == 422


def test_invalid_kind_shape_is_validation_error(settings):
    with pytest.raises(ValueError):
        settings.save({'cloudWorkflows': [workflow(kinds=[{}])]})


def test_custom_audio_keeps_voice_authorization():
    from app.generation_profiles import build_workflow_request
    template = workflow(kinds=['audio.tts'], mappings=[{'source': 'audio', 'nodeId': '1', 'fieldName': 'audio'},
                                                     {'source': 'prompt', 'nodeId': '2', 'fieldName': 'text'}])
    with pytest.raises(ValueError, match='授权'):
        build_workflow_request('audio.tts', {'prompt': 'hi'}, {'audio': [b'voice']}, template)
    request = build_workflow_request('audio.tts', {'prompt': 'hi', 'voiceAuthorized': True}, {'audio': [b'voice']}, template)
    assert request['user_data'][0]['fieldValue'] == b'voice'


def test_custom_fixed_seed_is_not_randomized(settings):
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'remote'}})
    template = workflow(nodeInfoList=[{'nodeId': '4', 'fieldName': 'seed', 'fieldValue': 42}])
    provider = RunningHub(key='test', settings=settings, client=httpx.Client(transport=httpx.MockTransport(handler)))
    provider.submit('image.generate', {'prompt': 'hello', '_workflow': template}, {})
    assert captured[0]['nodeInfoList'][0]['fieldValue'] == 42


def test_workflow_validation_endpoint_is_read_only(settings, tmp_path, monkeypatch):
    from app.main import create_app
    settings.save({'cloudWorkflows': [workflow('existing')]})
    original = settings.path.read_bytes()
    monkeypatch.setattr(RunningHub, 'submit', lambda *args: pytest.fail('validation must not submit'))
    with TestClient(create_app(tmp_path / 'projects', 'test-token', start_worker=False, settings=settings)) as client:
        url = '/api/v1/settings/workflows/validate'
        assert client.post(url, json=workflow()).status_code == 401
        client.headers['Authorization'] = 'Bearer test-token'
        result = client.post(url, json=workflow())
        assert result.status_code == 200
        assert result.json() == workflow()
        for invalid in [workflow(resultNodes=[]), workflow(kinds=[{}]),
                        workflow(mappings=[{'source': 'image', 'nodeId': {}, 'fieldName': 'image'}]),
                        workflow(apiKey='must-not-save')]:
            response = client.post(url, json=invalid)
            assert response.status_code == 422
            assert response.json()['message']
    assert settings.path.read_bytes() == original


@pytest.mark.parametrize('status,expected', [
    (400, 'PROVIDER_REJECTED'), (401, 'PROVIDER_AUTH'), (403, 'PROVIDER_AUTH'),
    (404, 'MODEL_UNAVAILABLE'), (422, 'PROVIDER_REJECTED'), (429, 'PROVIDER_RATE_LIMIT'),
    (500, 'TEXT_GENERATION_FAILED'), (200, 'TEXT_GENERATION_FAILED'),
])
def test_text_http_errors_are_classified(settings, monkeypatch, status, expected):
    settings.set_key('text', 'fake')
    real_client = httpx.Client
    def handler(request):
        return httpx.Response(status, json={'error': 'private-upstream-details'})
    monkeypatch.setattr('app.providers.httpx.Client', lambda **kw: real_client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ProviderError) as error:
        TextProvider(settings, 'https://example.invalid/v1', 'model').generate('script.expand', 'hello')
    assert error.value.code == expected
    assert 'private-upstream-details' not in str(error.value)


@pytest.mark.parametrize('status', [400, 401, 403, 404, 422, 429, 500])
def test_text_rejection_releases_cost_and_can_retry(tmp_path, settings, monkeypatch, status):
    settings.save({'textApiBase': 'https://example.invalid/v1', 'textModel': 'model',
                   'pricing': {'text/model': {'amount': '0.3', 'unit': 'task', 'currency': 'CNY'}}})
    settings.set_key('text', 'fake')
    store, project, worker, task = make_task(tmp_path, settings, 'script.expand', {})
    worker.mock = False
    calls = []
    real_client = httpx.Client
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={'error': 'rejected'}) if len(calls) == 1 else httpx.Response(200, json={'choices': [{'message': {'content': 'done'}}]})
    monkeypatch.setattr('app.providers.httpx.Client', lambda **kw: real_client(transport=httpx.MockTransport(handler)))
    worker.tick()
    failed = store.task(task['id'])
    reservation = worker.ledger.summary(project['id'])['reservations'][0]
    assert failed['status'] == 'failed'
    assert not worker.tick()  # 明确拒绝也不自动重发收费请求。
    assert len(calls) == 1
    if status == 500:
        assert failed['error_code'] == 'SUBMIT_UNCERTAIN'
        assert reservation['status'] == 'reserved'
        with pytest.raises(ValueError):
            worker.retry(task['id'])
    else:
        assert failed['error_code'] != 'SUBMIT_UNCERTAIN'
        assert reservation['status'] == 'released'
        assert worker.ledger.summary(project['id'])['estimatedUsed'] == {}
        worker.retry(task['id'])
        worker.tick()
        assert store.task(task['id'])['status'] == 'completed'
        assert worker.ledger.summary(project['id'])['estimatedUsed'] == {'CNY': '0.300000'}
        assert len(calls) == 2


def test_default_workflow_preflight_does_not_reserve_invalid_input(tmp_path, settings, monkeypatch):
    import io
    from PIL import Image
    store = Store(tmp_path / 'projects')
    project = store.create_project('Invalid input')
    project['settings']['cloudEnabled'] = True
    store.put_document(project['id'], 'project', project)
    png = io.BytesIO()
    Image.new('RGB', (8, 8)).save(png, 'PNG')
    asset = store.add_asset(project['id'], png.getvalue(), 'reference.png')
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [{'id': 'image', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'image.generate', 'config': {'prompt': 'hello', 'referenceIds': [asset['id']] * 9}}}]
    store.save_canvas(project['id'], canvas, canvas['version'])
    worker = Worker(store, settings=settings)
    monkeypatch.setattr(worker.provider, 'request', lambda *args, **kwargs: pytest.fail('invalid input must not contact provider'))
    worker.submit(project['id'])
    worker.tick()
    task = store.tasks(project['id'])[0]
    assert task['error_code'] == 'INVALID_INPUT'
    assert not task['submitted']
    assert worker.ledger.summary(project['id'])['reservations'] == []
