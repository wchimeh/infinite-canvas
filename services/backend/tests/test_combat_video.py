import itertools
import json
from pathlib import Path

import httpx
import pytest

from app.combat_video_workflow import build_combat_video_request
from app.generation_profiles import resolve_selection, build_workflow_request
from app.graph import DEFINITIONS
from app.providers import RunningHub
from generate_tool.minimax_h3_combat import WORKFLOW


def test_template_matches_original():
    source = Path(__file__).resolve().parents[3] / 'H3终极篇-文武05｜图生视频文戏武戏通吃的进阶版_api.json'
    assert WORKFLOW == json.loads(source.read_text(encoding='utf-8-sig'))


@pytest.mark.parametrize('images,audios,videos', list(itertools.product(range(1, 10), range(4), range(4))))
def test_all_reference_combinations(images, audios, videos):
    inputs = {p: [f'{p}-{i}'.encode() for i in range(n)] for p, n in [('image', images), ('audio', audios), ('video', videos)]}
    request = build_combat_video_request({'prompt': 'action'}, inputs)
    graph = request['workflow']
    assert request['result_node'] == ['364']
    uploads = {item['nodeId']: item for item in request['user_data'] if '_mediaType' in item}
    for port, items in inputs.items():
        prefix = f'ref_{port}s.ref_{port}_'
        assert sum(key.startswith(prefix) for key in graph['265']['inputs']) == len(items)
        for i, data in enumerate(items):
            loader, index = graph['265']['inputs'][prefix + str(i)]
            assert index == 0 and uploads[loader]['fieldValue'] == data
    assert len(uploads) == images + audios + videos
    for node_id, node in graph.items():
        if node['class_type'] in ('LoadImage', 'LoadAudio', 'VHS_LoadVideo'):
            assert node_id in uploads
        for value in node['inputs'].values():
            if isinstance(value, list) and len(value) == 2:
                assert value[0] in graph
    assert graph['192'] == WORKFLOW['192']
    assert graph['397']['inputs']['model'] == WORKFLOW['397']['inputs']['model']


def test_parameter_mapping_and_defaults():
    default = build_combat_video_request({}, {'image': [b'i']})
    graph = default['workflow']
    assert graph['261']['inputs']['steps'] == 10
    assert graph['343']['inputs']['strength_model'] == 1
    assert graph['342']['inputs']['strength_model'] == 0.35
    assert graph['397']['inputs']['transition_step'] == 6
    assert graph['252']['inputs']['megapixels'] == 0.5
    assert graph['397']['inputs']['cfg'] == 1
    config = {'prompt': 'fight', 'seconds': 12, 'combatH3': {'aspectRatio': '9:16 (Portrait Widescreen)', 'megapixels': 1,
        'steps': 16, 'transitionStep': 4, 'cfg': 2, 'seedMode': 'fixed', 'seed': 123, 'combatStrength': 0.9,
        'motionRepairStrength': 0.2, 'fightFlowStrength': 0.6, 'speedStrength': 3}}
    request = build_combat_video_request(config, {'image': [b'i']})
    g = request['workflow']
    assert g['252']['inputs']['aspect_ratio'] == config['combatH3']['aspectRatio']
    assert g['261']['inputs']['steps'] == 16 and g['397']['inputs']['cfg'] == 2
    assert g['397']['inputs']['transition_step'] == 4
    assert g['397']['inputs']['seed'] == 123
    assert [g[n]['inputs']['strength_model'] for n in ['342', '344', '345', '343']] == [0.9, 0.2, 0.6, 3]
    assert g['259']['inputs']['value'] == 12 and g['263']['inputs']['text'] == 'fight'


@pytest.mark.parametrize('config,inputs', [({}, {}), ({}, {'image': [b'i'] * 10}), ({}, {'image': [b'i'], 'audio': [b'a'] * 4}),
    ({}, {'image': [b'i'], 'video': [b'v'] * 4}), ({'combatH3': {'steps': True}}, {'image': [b'i']}),
    ({'combatH3': {'cfg': -1}}, {'image': [b'i']}), ({'seconds': 0}, {'image': [b'i']}),
    ({'combatH3': {'steps': 6}}, {'image': [b'i']}), ({'combatH3': {'transitionStep': 0}}, {'image': [b'i']}),
    ({'combatH3': {'transitionStep': 10}}, {'image': [b'i']}), ({'combatH3': {'transitionStep': 1.5}}, {'image': [b'i']}),
    ({'combatH3': {'transitionStep': True}}, {'image': [b'i']}),
    ({'combatH3': {'steps': 8, 'transitionStep': 8}}, {'image': [b'i']})])
def test_invalid_inputs(config, inputs):
    with pytest.raises(ValueError):
        build_combat_video_request(config, inputs)


def test_registration_and_real_submission_payload():
    definition = DEFINITIONS['video.combat']
    assert len(definition['inputs']) == 16 and definition['outputs'] == {'video': 'video'}
    profile = resolve_selection({}, 'video.combat', {})['cloudWorkflow']
    assert profile['builtin'] == 'minimax_h3_combat'
    calls, uploads = [], []
    def handle(request):
        if request.url.path.endswith('/upload'):
            uploads.append(request.content)
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': f'upload-{len(uploads)}'}})
        calls.append(json.loads(json.loads(request.content)['workflow']))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'combat-qa'}})
    provider = RunningHub(key='qa', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit('video.combat', {'_workflow': profile, 'prompt': 'fight', 'combatH3': {'seedMode': 'fixed', 'seed': 23}},
                           {'image': [b'image'], 'audio': [b'audio'], 'video': [b'video']}) == 'combat-qa'
    assert len(uploads) == 3 and calls[0]['397']['inputs']['seed'] == 23
    assert calls[0]['263']['inputs']['text'] == 'fight'
    assert build_workflow_request('video.combat', {}, {'image': [b'i']}, profile)['result_node'] == ['364']


def test_worker_orders_media_and_inherits_duration(tmp_path, monkeypatch):
    from test_text_input import setup
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='video.combat', config={})
    assets, data_by_source = {}, {}
    for port, extension, count in [('image', 'png', 9), ('audio', 'wav', 3), ('video', 'mp4', 3)]:
        for index in range(count, 0, -1):
            source = f'{port}{index}'
            data = source.encode()
            if port == 'image':
                import io
                from PIL import Image
                buffer = io.BytesIO()
                Image.new('RGB', (8, 8), (index * 20, 0, 0)).save(buffer, format='PNG')
                data = buffer.getvalue()
            data_by_source[source] = data
            assets[source] = store.add_asset(pid, data, source + '.' + extension)
            canvas['nodes'].append({'id': source, 'type': 'studio', 'position': {'x': 0, 'y': 0},
                                   'data': {'kind': 'asset.' + port, 'config': {'assetId': assets[source]['id']}}})
            canvas['edges'].append({'id': source, 'source': source, 'sourceHandle': port, 'target': 'script',
                                   'targetHandle': port + (str(index) if index > 1 else ''), 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] == 'story':
            store.update_task(task['id'], status='completed', output={'text': 'fight', 'seconds': 12})
        elif task['node_id'] in assets:
            store.update_task(task['id'], status='completed', output={'assets': [assets[task['node_id']]['id']]})
    task = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    config, inputs, _ = worker.inputs(task)
    assert config['seconds'] == 12
    for port, count in [('image', 9), ('audio', 3), ('video', 3)]:
        assert inputs[port] == [data_by_source[f'{port}{i}'] for i in range(1, count + 1)]
    assert config['_workflow']['builtin'] == 'minimax_h3_combat'
    task['snapshot']['config']['seconds'] = 6
    assert worker.inputs(task)[0]['seconds'] == 6


def test_cost_defaults_and_result_download(monkeypatch):
    from app.costs import quote_snapshot
    profile = resolve_selection({}, 'video.combat', {})['cloudWorkflow']
    quote = quote_snapshot({'kind': 'video.combat', 'config': {}, 'cloudWorkflow': profile},
                           {'workflow/' + profile['id']: {'amount': '1', 'unit': 'second', 'currency': 'CNY'}})
    assert quote['amount'] == '8.000000'
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b'video-result')))
    provider = RunningHub(key='qa', client=client)
    monkeypatch.setattr(provider, 'request', lambda *args: [{'nodeId': '364', 'fileUrl': 'https://www.runninghub.cn/qa.mp4', 'fileType': 'mp4'}])
    assert provider.fetch('qa', 'video.combat', {'_workflow': profile}, {'image': [b'i']}) == [(b'video-result', 'qa.mp4')]


@pytest.mark.parametrize('steps', [7, 10, 16, 1000])
def test_selflift_default_transition_step(steps):
    graph = build_combat_video_request({'combatH3': {'steps': steps}}, {'image': [b'i'], 'video': [b'v']})['workflow']
    assert graph['261']['inputs']['steps'] == steps
    assert graph['397']['inputs']['transition_step'] == 6 < steps
    video_loader = graph['265']['inputs']['ref_videos.ref_video_0'][0]
    assert graph[video_loader]['inputs']['force_rate'] == 24


@pytest.mark.parametrize('steps,transition', [(2, 1), (6, 5), (7, 6), (10, 3), (16, 15)])
def test_selflift_explicit_transition_step(steps, transition):
    graph = build_combat_video_request({'combatH3': {'steps': steps, 'transitionStep': transition}}, {'image': [b'i']})['workflow']
    assert graph['261']['inputs']['steps'] == steps
    assert graph['397']['inputs']['transition_step'] == transition < steps


def test_selflift_rejects_one_step_and_cache_version_changes():
    with pytest.raises(ValueError, match='steps'):
        build_combat_video_request({'combatH3': {'steps': 1}}, {'image': [b'i']})
    assert resolve_selection({}, 'video.combat', {})['cloudWorkflow']['version'] == 3
