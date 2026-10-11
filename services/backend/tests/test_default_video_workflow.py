import copy
import json

import httpx
import pytest

from app.generation_profiles import build_workflow_request, resolve_selection
from app.providers import RunningHub
from generate_tool import rh_process_generate, workflow_json_new


@pytest.mark.parametrize('count', range(1, 10))
@pytest.mark.parametrize('extra', ['', 'audio', 'video'])
def test_all_file_templates_match_actual_counts(count, extra):
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    inputs = {'image': [f'image{i}'.encode() for i in range(count)]}
    if extra:
        inputs[extra] = [extra.encode()]
    name = f'minimax_h3_{count}_image' + (f'_1_{extra}' if extra else '') + '_json'
    original = copy.deepcopy(getattr(workflow_json_new, name))
    request = build_workflow_request('video.image_to_video', {'prompt': 'new scene', 'seconds': 7}, inputs, profile)
    graph = request['workflow']
    assert graph['115']['inputs']['megapixels'] == 0.4
    assert request['result_node'] == ['271']
    assert len([key for key in graph['136']['inputs'] if key.startswith('ref_images.')]) == count
    assert len([node for node in graph.values() if node['class_type'] == 'LoadImage']) == count
    assert [entry['fieldValue'] for entry in request['user_data'] if entry.get('_mediaType') == 'image'] == inputs['image']
    assert len([entry for entry in request['user_data'] if entry.get('_mediaType') in ('video', 'audio')]) == bool(extra)
    assert next(entry['fieldValue'] for entry in request['user_data'] if entry['nodeId'] == '132') == 7
    assert graph['138']['inputs']['value'] == ''
    assert getattr(workflow_json_new, name) == original


@pytest.mark.parametrize('inputs', [{}, {'image': [b'i'] * 10}, {'image': [b'i'], 'audio': [b'a'] * 2}, {'image': [b'i'], 'video': [b'v'] * 2}, {'image': [b'i'], 'video': [b'v'], 'audio': [b'a']}])
def test_missing_templates_rejected_without_dropping_media(inputs):
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    with pytest.raises(ValueError):
        build_workflow_request('video.image_to_video', {'prompt': 'scene'}, inputs, profile)


def test_default_calls_complete_workflow_method_and_replaces_examples(monkeypatch):
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    original = rh_process_generate.rh_api_generate_by_workflow
    called, requests, uploads = [], [], []
    def spy(graph, *args, **kwargs):
        called.append(copy.deepcopy(graph))
        return original(graph, *args, **kwargs)
    monkeypatch.setattr(rh_process_generate, 'rh_api_generate_by_workflow', spy)
    def handle(request):
        if request.url.path.endswith('/upload'):
            uploads.append(request.content)
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': f'uploaded-{len(uploads)}'}})
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'matched'}})
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit('video.image_to_video', {'prompt': 'actual prompt', 'seconds': 8, '_workflow': profile}, {'image': [b'first', b'second'], 'audio': [b'voice']}) == 'matched'
    assert len(called) == len(requests) == 1 and len(uploads) == 3
    graph = json.loads(requests[0]['workflow'])
    assert graph['115']['inputs']['megapixels'] == 0.4
    assert graph == called[0]
    assert graph['138']['inputs']['value'] == 'actual prompt'
    assert graph['132']['inputs']['value'] == 8
    assert graph['139']['inputs']['image'] == 'uploaded-1'
    assert graph['256']['inputs']['image'] == 'uploaded-2'
    assert graph['275']['inputs']['audio'] == 'uploaded-3'
