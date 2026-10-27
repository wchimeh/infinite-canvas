import copy
import json
import itertools
from pathlib import Path

import httpx
import pytest

from app.generation_profiles import build_workflow_request, resolve_selection
from app.providers import RunningHub
from generate_tool import rh_process_generate
from generate_tool.minimax_h3_all import WORKFLOW


def test_builtin_template_equals_supplied_json():
    source = Path(__file__).resolve().parents[3] / 'MiniMax H3全能参考生视频（动作迁移）_api全部.json'
    assert WORKFLOW == json.loads(source.read_text(encoding='utf-8-sig'))


@pytest.mark.parametrize('counts', [c for c in itertools.product(range(10), range(4), range(4), range(4)) if any(c)])
def test_all_four_reference_count_combinations(counts):
    from app.video_workflow import build_default_video_request
    ports = ['image', 'video', 'audio', 'video_audio']
    prefixes = ['ref_images.ref_image_', 'ref_videos.ref_video_', 'ref_audios.ref_audio_', 'ref_video_audios.ref_video_audio_']
    inputs = {p: [f'{p}{i}'.encode() for i in range(count)] for p, count in zip(ports, counts)}
    result = build_default_video_request({}, inputs)
    graph = result['workflow']
    mappings = {v['nodeId']: v for v in result['user_data'] if '_mediaType' in v}
    for port, prefix, count in zip(ports, prefixes, counts):
        keys = [k for k in graph['136']['inputs'] if k.startswith(prefix)]
        assert len(keys) == count
        for i in range(count):
            node_id, output = graph['136']['inputs'][prefix + str(i)]
            assert output == 0
            assert mappings[node_id]['fieldValue'] == inputs[port][i]
    for node in graph.values():
        for value in node['inputs'].values():
            if isinstance(value, list) and len(value) == 2:
                assert value[0] in graph
    for node_id, node in graph.items():
        for field in ['image', 'audio', 'video']:
            if node['class_type'] in ['LoadImage', 'LoadAudio', 'VHS_LoadVideo'] and field in node['inputs']:
                assert node['inputs'][field] == '' and node_id in mappings


def test_same_audio_reuses_loader_across_audio_groups():
    from app.video_workflow import build_default_video_request
    result = build_default_video_request({}, {'video': [b'v1', b'v2'], 'audio': [b'shared'], 'video_audio': [b'shared', b'other']})
    inputs = result['workflow']['136']['inputs']
    assert inputs['ref_audios.ref_audio_0'][0] == inputs['ref_video_audios.ref_video_audio_0'][0]
    assert len([v for v in result['user_data'] if v.get('_mediaType') == 'audio']) == 2


@pytest.mark.parametrize('inputs,expected', [
    ({'image': [b'one']}, {'ref_images.ref_image_0'}),
    ({'image': [b'one', b'two'], 'audio': [b'voice1', b'voice2']},
     {'ref_images.ref_image_0', 'ref_images.ref_image_1', 'ref_audios.ref_audio_0', 'ref_audios.ref_audio_1'}),
    ({'video': [b'frames'], 'audio': [b'voice'], 'video_audio': [b'movie']}, {'ref_videos.ref_video_0', 'ref_audios.ref_audio_0', 'ref_video_audios.ref_video_audio_0'}),
])
def test_only_explicit_reference_inputs_are_retained(inputs, expected):
    from app.video_workflow import build_default_video_request
    graph = build_default_video_request({}, inputs)['workflow']
    assert {key for key in graph['136']['inputs'] if key.startswith('ref_') and '.' in key} == expected
    if not inputs.get('video'):
        assert not any(node['class_type'] == 'VHS_LoadVideo' for node in graph.values())


def test_full_reference_payload_reaches_cloud_without_sample_files():
    sent, uploads = [], []
    def handle(request):
        if request.url.path.endswith('/upload'):
            uploads.append(request.content)
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': f'upload-{len(uploads)}'}})
        sent.append(json.loads(json.loads(request.content)['workflow']))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'full'}})
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    inputs = {p: [f'{p}{i}'.encode() for i in range(n)] for p, n in [('image', 9), ('video', 3), ('audio', 3), ('video_audio', 3)]}
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit('video.image_to_video', {'prompt': 'action', 'seconds': 10, '_workflow': profile}, inputs) == 'full'
    assert len(uploads) == 18
    assert sent[0]['144']['inputs']['prompt'] == 'action'
    assert sent[0]['132']['inputs']['value'] == 10
    for node in sent[0].values():
        if node['class_type'] in ['LoadImage', 'LoadAudio', 'VHS_LoadVideo']:
            field = {'LoadImage': 'image', 'LoadAudio': 'audio', 'VHS_LoadVideo': 'video'}[node['class_type']]
            assert node['inputs'][field].startswith('upload-')


@pytest.mark.parametrize('version,node_id', [(1, '271'), (1, '92'), (2, '92')])
def test_existing_remote_task_download_survives_template_upgrade(version, node_id):
    calls = []
    def handle(request):
        calls.append(request.url.path)
        if request.method == 'GET':
            return httpx.Response(200, content=b'video-bytes')
        assert json.loads(request.content)['taskId'] == 'existing-task'
        assert not request.url.path.endswith(('/upload', '/create'))
        return httpx.Response(200, json={'code': 0, 'data': [
            {'nodeId': node_id, 'fileUrl': 'https://www.runninghub.cn/result.mp4', 'fileType': 'mp4'}]})
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    profile['version'] = version
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    results = provider.fetch('existing-task', 'video.image_to_video', {'_workflow': profile}, {'image': [b'i']})
    assert results[0][0] == b'video-bytes'
    assert len(calls) == 2


@pytest.mark.parametrize('count', range(1, 10))
@pytest.mark.parametrize('extra', ['', 'audio', 'video'])
def test_all_file_templates_match_actual_counts(count, extra):
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    inputs = {'image': [f'image{i}'.encode() for i in range(count)]}
    if extra:
        inputs[extra] = [extra.encode()]

    original = copy.deepcopy(WORKFLOW)
    request = build_workflow_request('video.image_to_video', {'prompt': 'new scene', 'seconds': 7}, inputs, profile)
    graph = request['workflow']
    assert graph['115']['inputs']['megapixels'] == 0.4
    assert graph['115']['inputs']['aspect_ratio'] == '16:9 (Widescreen)'
    assert graph['115']['inputs']['multiple'] == 32
    assert graph['124']['inputs']['steps'] == 8
    assert request['result_node'] == ['92']
    assert len([key for key in graph['136']['inputs'] if key.startswith('ref_images.')]) == count
    assert len([node for node in graph.values() if node['class_type'] == 'LoadImage']) == count
    assert [entry['fieldValue'] for entry in request['user_data'] if entry.get('_mediaType') == 'image'] == inputs['image']
    assert len([entry for entry in request['user_data'] if entry.get('_mediaType') in ('video', 'audio')]) == bool(extra)
    assert next(entry['fieldValue'] for entry in request['user_data'] if entry['nodeId'] == '132') == 7
    assert graph['144']['inputs']['prompt'] == ''
    assert WORKFLOW == original


@pytest.mark.parametrize('inputs', [{}, {'image': [b'i'] * 10}, {'image': [b'i'], 'audio': [b'a'] * 4}, {'image': [b'i'], 'video': [b'v'] * 4}, {'video_audio': [b'v'] * 4}])
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
    assert graph['144']['inputs']['prompt'] == 'actual prompt'
    assert graph['132']['inputs']['value'] == 8
    assert graph['137']['inputs']['image'] == 'uploaded-1'
    assert graph['139']['inputs']['image'] == 'uploaded-2'
    assert graph['180']['inputs']['audio'] == 'uploaded-3'


@pytest.mark.parametrize('count', range(1, 10))
@pytest.mark.parametrize('extra', ['', 'audio', 'video'])
def test_minimax_parameters_override_all_templates(count, extra):
    from app.video_workflow import build_default_video_request
    settings = {'aspectRatio': '9:16 (Portrait Widescreen)', 'megapixels': 0.8, 'multiple': 64,
                'steps': 12, 'seedMode': 'fixed', 'seed': 0}
    inputs = {'image': [b'i'] * count, **({extra: [b'ref']} if extra else {})}
    request = build_default_video_request({'minimaxH3': settings}, inputs)
    assert request['workflow']['115']['inputs'] == {'aspect_ratio': settings['aspectRatio'], 'megapixels': 0.8, 'multiple': 64}
    assert request['workflow']['124']['inputs']['steps'] == 12
    assert next(v['fieldValue'] for v in request['user_data'] if v['nodeId'] == '129') == 0


def test_minimax_random_seed_and_final_cloud_payload(monkeypatch):
    from app.video_workflow import build_default_video_request
    seeds = iter([123, 456])
    monkeypatch.setattr('app.video_workflow.secrets.randbelow', lambda maximum: next(seeds))
    for seed in [123, 456]:
        request = build_default_video_request({}, {'image': [b'i']})
        assert next(v['fieldValue'] for v in request['user_data'] if v['nodeId'] == '129') == seed
    sent = []
    def handle(request):
        if request.url.path.endswith('/upload'):
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'image.png'}})
        sent.append(json.loads(json.loads(request.content)['workflow']))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'configured'}})
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    config = {'_workflow': profile, 'minimaxH3': {'megapixels': 0.7, 'multiple': 64, 'steps': 8, 'seedMode': 'fixed', 'seed': 2147483646}}
    assert provider.submit('video.image_to_video', config, {'image': [b'i']}) == 'configured'
    assert sent[0]['129']['inputs']['noise_seed'] == 2147483646
    assert sent[0]['124']['inputs']['steps'] == 8
    assert sent[0]['115']['inputs']['megapixels'] == 0.7
    assert sent[0]['115']['inputs']['multiple'] == 64


@pytest.mark.parametrize('settings', [None, [], {'megapixels': 0}, {'megapixels': float('nan')},
    {'multiple': 1.5}, {'multiple': True}, {'steps': 0}, {'steps': '8'}, {'seedMode': 'unknown'},
    {'seedMode': 'fixed', 'seed': -1}, {'seedMode': 'fixed', 'seed': 2147483647},
    {'seedMode': 'fixed', 'seed': True}, {'seedMode': 'fixed'}, {'aspectRatio': ''}, {'aspectRatio': '16:9'}])
def test_minimax_invalid_parameters_rejected_before_upload(settings):
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    def unexpected(request):
        pytest.fail('Invalid parameters must not upload or submit')
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(unexpected)))
    with pytest.raises(ValueError):
        provider.submit('video.image_to_video', {'_workflow': profile, 'minimaxH3': settings}, {'image': [b'i']})


@pytest.mark.parametrize('ratio', ['1:1 (Square)', '2:3 (Portrait Photo)', '3:2 (Photo)',
    '3:4 (Portrait Standard)', '4:3 (Standard)', '9:16 (Portrait Widescreen)',
    '16:9 (Widescreen)', '21:9 (Ultrawide)'])
def test_all_supported_minimax_ratios(ratio):
    from app.video_workflow import build_default_video_request
    request = build_default_video_request({'minimaxH3': {'aspectRatio': ratio}}, {'image': [b'i']})
    assert request['workflow']['115']['inputs']['aspect_ratio'] == ratio


def test_orphan_video_audio_is_uploaded_and_forwarded():
    uploads, submitted = [], []
    def handle(request):
        if request.url.path.endswith('/upload'):
            uploads.append(request.content)
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'uploaded-voice.wav'}})
        submitted.append(json.loads(json.loads(request.content)['workflow']))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'orphan-audio'}})
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    profile = resolve_selection({}, 'video.image_to_video', {})['cloudWorkflow']
    provider.submit('video.image_to_video', {'prompt': 'scene', '_workflow': profile}, {'video_audio': [b'voice-content']})
    graph = submitted[0]
    node = graph['136']['inputs']['ref_video_audios.ref_video_audio_0'][0]
    assert graph[node]['inputs']['audio'] == 'uploaded-voice.wav'
    assert len(uploads) == 1 and b'voice-content' in uploads[0]
    assert not any(key.startswith('ref_videos.') for key in graph['136']['inputs'])
