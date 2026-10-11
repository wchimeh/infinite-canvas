import copy
import json

import httpx
import pytest

from app.generation_profiles import build_workflow_request, validate_workflow
from app.providers import ProviderError, RunningHub
from generate_tool import rh_process_generate


def profile(kind='image.generate'):
    return {'id': 'full', 'name': 'Full', 'version': 1, 'enabled': True, 'kinds': [kind],
            'workflow': {
                '1': {'class_type': 'Text', 'inputs': {'text': 'original', 'steps': 20}},
                '2': {'class_type': 'LoadImage', 'inputs': {'image': 'old.png'}},
                '3': {'class_type': 'Save', 'inputs': {'text': ['1', 0], 'images': ['2', 0]}},
            }, 'mappings': [{'source': 'prompt', 'nodeId': '1', 'fieldName': 'text'},
                            {'source': 'image', 'nodeId': '2', 'fieldName': 'image'}],
            'resultNodes': ['3']}


@pytest.mark.parametrize('kind', ['image.generate', 'video.image_to_video'])
@pytest.mark.parametrize('as_string', [False, True])
def test_full_submission_calls_script_preserves_graph_and_uploads(kind, as_string, monkeypatch):
    value = profile(kind)
    if as_string:
        value['workflow'] = json.dumps(value['workflow'])
    before = copy.deepcopy(value)
    requests, calls = [], []
    original = rh_process_generate.rh_api_generate_by_workflow

    def spy(*args, **kwargs):
        calls.append(copy.deepcopy(args[0]))
        return original(*args, **kwargs)

    monkeypatch.setattr(rh_process_generate, 'rh_api_generate_by_workflow', spy)

    def handle(request):
        if request.url.path.endswith('/upload'):
            assert b'asset-bytes' in request.content
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'uploaded.png'}})
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'task-1'}})

    provider = RunningHub(key='test-key', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit(kind, {'_workflow': value, 'prompt': 'new prompt'}, {'image': [b'asset-bytes']}) == 'task-1'
    assert value == before
    assert len(calls) == len(requests) == 1
    body = requests[0]
    assert body['apiKey'] == 'test-key'
    assert body['workflowId'] == rh_process_generate.PLACEHOLDER_WORKFLOW_ID
    assert 'nodeInfoList' not in body
    graph = json.loads(body['workflow'])
    assert graph == calls[0]
    assert graph['1']['inputs'] == {'text': 'new prompt', 'steps': 20}
    assert graph['2']['inputs']['image'] == 'uploaded.png'
    assert graph['3']['inputs'] == {'text': ['1', 0], 'images': ['2', 0]}


@pytest.mark.parametrize('mutation', [
    lambda p: p.update(workflow='invalid'),
    lambda p: p.update(workflow={'nodes': []}),
    lambda p: p.update(resultNodes=['missing']),
    lambda p: p['mappings'][0].update(fieldName='missing'),
    lambda p: p['workflow']['3']['inputs'].update(text=['missing', 0]),
    lambda p: p['workflow']['1']['inputs'].update(api_key='secret'),
])
def test_invalid_full_graph_rejected(mutation):
    value = profile()
    mutation(value)
    with pytest.raises(ValueError):
        validate_workflow(value)


@pytest.mark.parametrize('status,body,code', [
    (401, {}, 'PROVIDER_AUTH'), (429, {}, 'PROVIDER_RATE_LIMIT'),
    (500, {}, 'PROVIDER_UNAVAILABLE'),
    (200, {'code': 0, 'data': {}}, 'SUBMIT_UNCERTAIN'),
    (200, {'code': 1, 'msg': 'bad graph'}, 'PROVIDER_REJECTED'),
])
def test_full_graph_retains_error_classification(status, body, code):
    value = profile()
    value['mappings'] = []
    provider = RunningHub(key='test', client=httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json=body))))
    with pytest.raises(ProviderError) as error:
        provider.submit('image.generate', {'_workflow': value}, {})
    assert error.value.code == code


def test_request_graph_is_independent_and_explicit_id_retained():
    value = profile()
    value['workflowId'] = 'custom-id'
    result = build_workflow_request('image.generate', {}, {'image': [b'image']}, value)
    result['workflow']['1']['inputs']['steps'] = 42
    assert value['workflow']['1']['inputs']['steps'] == 20
    assert result['workflowId'] == 'custom-id'


def test_original_script_call_still_supported(monkeypatch):
    recorded = []
    def post(url, **kwargs):
        recorded.append(kwargs['json'])
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'old-call'}})
    monkeypatch.setattr(rh_process_generate.requests, 'post', post)
    assert rh_process_generate.rh_api_generate_by_workflow(profile()['workflow'], 'explicit') == 'old-call'
    assert recorded[0]['workflowId'] == 'explicit'
