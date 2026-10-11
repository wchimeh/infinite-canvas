import json
import io

import httpx
import pytest
from PIL import Image

from app.generation_profiles import validate_workflow, build_workflow_request, resolve_selection, workflow_catalog
from app.providers import RunningHub
from test_text_input import setup


def omni():
    return {'id': 'omni', 'name': '全能参考', 'enabled': True, 'version': 1,
            'kinds': ['video.image_to_video'],
            'workflow': {'1': {'class_type': 'Omni', 'inputs': {'text': '', 'video': '', 'audio': ''}}},
            'mappings': [{'source': source, 'nodeId': '1', 'fieldName': field}
                         for source, field in [('prompt', 'text'), ('video', 'video'), ('audio', 'audio')]],
            'resultNodes': ['1']}


@pytest.mark.parametrize('linked', [False, True])
def test_video_audio_references_without_image_reach_full_workflow(tmp_path, monkeypatch, linked):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; template = omni(); validate_workflow(template)
    worker.settings.save({'cloudWorkflows': [template]})
    assets = {port: store.add_asset(pid, port.encode(), filename) for port, filename in [('video', 'ref.mp4'), ('audio', 'ref.wav')]}
    canvas = store.canvas(pid); canvas['nodes'][1]['data'].update(kind='video.image_to_video', config={'workflowId': 'omni'})
    if linked:
        for port, asset in assets.items():
            canvas['nodes'].append({'id': port, 'type': 'studio', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'asset.' + port, 'config': {'assetId': asset['id']}}})
            canvas['edges'].append({'id': port, 'source': port, 'target': 'script', 'sourceHandle': port, 'targetHandle': port, 'data': {'kind': 'data'}})
    else:
        canvas['nodes'][1]['data']['config']['referenceIds'] = [asset['id'] for asset in assets.values()]
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] == 'story':
            store.update_task(task['id'], status='completed', output={'text': 'cinematic scene'})
        elif task['node_id'] in assets:
            store.update_task(task['id'], status='completed', output={'assets': [assets[task['node_id']]['id']]})
    target = next(task for task in store.run(run['id'])['tasks'] if task['node_id'] == 'script')
    config, inputs, _ = worker.inputs(target)
    assert inputs == {'video': [b'video'], 'audio': [b'audio']}
    requests = []
    def handle(request):
        if request.url.path.endswith('/upload'):
            return httpx.Response(200, json={'code': 0, 'data': {'fileName': 'uploaded'}})
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={'code': 0, 'data': {'taskId': 'remote'}})
    provider = RunningHub(key='test', client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert provider.submit('video.image_to_video', config, inputs) == 'remote'
    fields = json.loads(requests[0]['workflow'])['1']['inputs']
    assert fields == {'text': 'cinematic scene', 'video': 'uploaded', 'audio': 'uploaded'}


def test_full_video_accepts_all_media_mappings():
    template = omni()
    template['workflow']['1']['inputs']['image'] = ''
    template['mappings'].append({'source': 'image', 'nodeId': '1', 'fieldName': 'image'})
    validate_workflow(template)
    request = build_workflow_request('video.image_to_video', {'prompt': 'scene'}, {port: [port.encode()] for port in ('image', 'video', 'audio')}, template)
    assert {item['_mediaType'] for item in request['user_data'] if '_mediaType' in item} == {'image', 'video', 'audio'}


@pytest.mark.parametrize('custom', [False, True])
def test_video_required_media_still_checked(tmp_path, monkeypatch, custom):
    store, project, worker = setup(tmp_path, monkeypatch)
    worker.settings.save({'cloudWorkflows': [omni()]})
    canvas = store.canvas(project['id'])
    canvas['nodes'][1]['data'].update(kind='video.image_to_video', config={'workflowId': 'omni' if custom else 'builtin-ltx23'})
    store.save_canvas(project['id'], canvas, canvas['version'])
    with pytest.raises(ValueError, match='缺少 video' if custom else '所选工作流不存在'):
        worker.submit(project['id'], ['script'])


@pytest.mark.parametrize('config', [{'workflowId': 'builtin-ltx23'}, {'workflowId': 'builtin-wan22'}, {'workflowId': 'old-copy'}])
def test_new_video_generation_never_falls_back_to_legacy_models(config):
    settings = {'cloudWorkflows': [omni(), {'id': 'old-copy', 'name': 'Copy', 'builtin': 'ltx23', 'version': 1, 'enabled': True, 'kinds': ['video.image_to_video']}]}
    with pytest.raises(ValueError, match='工作流'):
        resolve_selection(settings, 'video.image_to_video', config)
    catalog = workflow_catalog(settings)
    assert [item['id'] for item in catalog if 'video.image_to_video' in item['kinds']] == ['builtin-minimax-h3', 'omni']
    assert resolve_selection(settings, 'video.image_to_video', {'workflowId': 'omni'})['cloudWorkflow']['id'] == 'omni'
    assert resolve_selection(settings, 'video.image_to_video', {'provider': 'comfyui'}) == {}


def test_worker_uses_default_and_rejects_missing_images_before_provider(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    canvas = store.canvas(project['id']); canvas['nodes'][1]['data']['kind'] = 'video.image_to_video'
    store.save_canvas(project['id'], canvas, canvas['version'])
    run = worker.submit(project['id'], ['script'])
    target = next(task for task in store.run(run['id'])['tasks'] if task['node_id'] == 'script')
    assert target['snapshot']['cloudWorkflow']['builtin'] == 'minimax_h3'
    worker.tick(); worker.tick()
    target = store.task(target['id'])
    assert target['status'] == 'failed' and target['submitted'] == 0
    assert '1–9' in target['error']


@pytest.mark.parametrize('extra_reference', [False, True])
@pytest.mark.parametrize('port,extension', [('image', 'png'), ('audio', 'wav'), ('video', 'mp4')])
def test_numbered_images_ordered_before_selected_references(tmp_path, monkeypatch, extra_reference, port, extension):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    count = 3 if extra_reference else 2
    template = omni()
    template['workflow']['1']['inputs'] = {'text': '', **{f'image{i}': '' for i in range(count)}}
    template['mappings'] = [{'source': 'prompt', 'nodeId': '1', 'fieldName': 'text'},
                            *[{'source': port, 'index': i, 'nodeId': '1', 'fieldName': f'image{i}'} for i in range(count)]]
    worker.settings.save({'cloudWorkflows': [template]})
    assets, contents = [], []
    for i in range(count):
        data = io.BytesIO(); Image.new('RGB', (2, 2), (i * 80, 0, 0)).save(data, format='PNG')
        contents.append(data.getvalue()); assets.append(store.add_asset(pid, contents[-1], f'image{i}.{extension}'))
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='video.image_to_video', config={'workflowId': 'omni', 'referenceIds': [assets[2]['id']] if extra_reference else []})
    # Connect reference 2 first to ensure connection creation order cannot reorder images.
    for i in [1, 0]:
        nid = f'picture{i}'
        canvas['nodes'].append({'id': nid, 'type': 'studio', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'asset.' + port, 'config': {'assetId': assets[i]['id']}}})
        canvas['edges'].append({'id': nid, 'source': nid, 'target': 'script', 'sourceHandle': port, 'targetHandle': port + '2' if i == 1 else port, 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] == 'story':
            store.update_task(task['id'], status='completed', output={'text': 'scene'})
        elif task['node_id'].startswith('picture'):
            store.update_task(task['id'], status='completed', output={'assets': [assets[int(task['node_id'][-1])]['id']]})
    target = next(task for task in store.run(run['id'])['tasks'] if task['node_id'] == 'script')
    config, inputs, _ = worker.inputs(target)
    assert inputs[port] == contents
    request = build_workflow_request('video.image_to_video', config, inputs, template)
    assert [entry['fieldValue'] for entry in request['user_data'] if entry.get('_mediaType') == port] == contents
    assert [entry['fieldName'] for entry in request['user_data'] if entry.get('_mediaType') == port] == [f'image{i}' for i in range(count)]


@pytest.mark.parametrize('port,limit', [('image', 9), ('audio', 3), ('video', 3)])
def test_video_mapping_limits(port, limit):
    template = omni()
    template['workflow']['1']['inputs'] = {'media': ''}
    template['mappings'] = [{'source': port, 'index': limit - 1, 'nodeId': '1', 'fieldName': 'media'}]
    validate_workflow(template)
    template['mappings'][0]['index'] = limit
    with pytest.raises(ValueError, match='索引'):
        validate_workflow(template)


@pytest.mark.parametrize('port,limit', [('image', 9), ('audio', 3), ('video', 3)])
def test_video_actual_media_limit_before_cloud_submission(tmp_path, monkeypatch, port, limit):
    from unittest.mock import Mock
    from app.worker import Worker
    path = tmp_path / 'media'; path.write_bytes(b'reference')
    store = Mock()
    store.task.return_value = {'node_id': 'upstream', 'output': {'assets': ['asset'] * limit}}
    store.asset_path.return_value = path
    store.asset.return_value = {'mime': port + '/fixture', 'sha256': 'hash'}
    worker = Worker(store)
    snap = {'kind': 'video.image_to_video', 'config': {'prompt': 'scene'}, 'references': [],
            'links': [{'source': 'upstream', 'port': port}], 'adapterVersion': 'qa', 'textModel': '', 'textEndpoint': ''}
    task = {'snapshot': snap, 'deps': ['upstream']}
    assert len(worker.inputs(task)[1][port]) == limit
    snap['references'] = [{'id': 'additional', 'mime': port + '/fixture'}]
    with pytest.raises(ValueError, match='合计超限'):
        worker.inputs(task)
