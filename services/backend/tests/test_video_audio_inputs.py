import copy
import pytest

from app.graph import DEFINITIONS, validate_graph
from app.generation_profiles import build_workflow_request, resolve_selection
from test_text_input import setup


def test_video_audio_ports_route_separately_and_in_numeric_order(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='video.image_to_video', config={'prompt': 'action'})
    assets = {}
    for index in range(3, 0, -1):
        source = f'v{index}'
        assets[source] = store.add_asset(pid, f'audio{index}'.encode(), f'{index}.wav')
        canvas['nodes'].append({'id': source, 'type': 'studio', 'position': {'x': 0, 'y': 0},
                               'data': {'kind': 'asset.audio', 'config': {'assetId': assets[source]['id']}}})
        for port in ['videoAudio', 'audio']:
            canvas['edges'].append({'id': port + source, 'source': source, 'sourceHandle': 'audio',
                                    'target': 'script', 'targetHandle': port + (str(index) if index > 1 else ''), 'data': {'kind': 'data'}})
    for index in range(1, 4):
        source = f'video{index}'
        assets[source] = store.add_asset(pid, f'video{index}'.encode(), f'{index}.mp4')
        canvas['nodes'].append({'id': source, 'type': 'studio', 'position': {'x': 0, 'y': 0},
                               'data': {'kind': 'asset.video', 'config': {'assetId': assets[source]['id']}}})
        canvas['edges'].append({'id': source, 'source': source, 'sourceHandle': 'video',
                               'target': 'script', 'targetHandle': 'video' + (str(index) if index > 1 else ''), 'data': {'kind': 'data'}})
    assert not validate_graph(canvas['nodes'], canvas['edges'])['errors']
    assert len(DEFINITIONS['video.image_to_video']['inputs']) == 19
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] == 'story':
            store.update_task(task['id'], status='completed', output={'text': 'scene'})
        elif task['node_id'] in assets:
            store.update_task(task['id'], status='completed', output={'assets': [assets[task['node_id']]['id']]})
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    config, inputs, cache_key = worker.inputs(target)
    assert config['_videoAudioVideoIndices'] == [0, 1, 2]
    assert inputs == {'video': [b'video1', b'video2', b'video3'], 'audio': [b'audio1', b'audio2', b'audio3'], 'video_audio': [b'audio1', b'audio2', b'audio3']}
    assert target['snapshot']['cloudWorkflow']['version'] == 2
    altered = copy.deepcopy(target)
    altered['snapshot']['links'] = [link for link in altered['snapshot']['links'] if link['port'] != 'video_audio']
    assert worker.inputs(altered)[2] != cache_key
    overflow = copy.deepcopy(target)
    overflow['snapshot']['links'].append({'source': 'v1', 'port': 'video_audio'})
    with pytest.raises(ValueError, match='3.*video_audio'):
        worker.inputs(overflow)
    request = build_workflow_request('video.image_to_video', config, inputs, config['_workflow'])
    assert len([v for v in request['user_data'] if v.get('_mediaType') == 'audio']) == 3


def test_video_audio_rejects_video_source_and_unsupported_workflow():
    nodes = [{'id': 'a', 'data': {'kind': 'asset.video'}}, {'id': 'v', 'data': {'kind': 'video.image_to_video'}}]
    edges = [{'id': 'e', 'source': 'a', 'sourceHandle': 'video', 'target': 'v', 'targetHandle': 'videoAudio'}]
    assert validate_graph(nodes, edges)['errors']
    with pytest.raises(ValueError, match='视频音频'):
        build_workflow_request('video.image_to_video', {}, {'video_audio': [b'video']}, None)
