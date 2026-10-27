import base64
import io
import wave

import httpx
import pytest

from app.expansion_media import media_content
from app.exporter import binary, command, probe
from app.graph import DEFINITIONS
from app.providers import ProviderError, TextProvider
from app.shot_nodes import validate_expansion_inputs
from test_text_input import setup
from test_shot_nodes import REWRITE


@pytest.fixture
def media(tmp_path):
    audio = tmp_path / 'audio.wav'
    video = tmp_path / 'video.mp4'
    command([binary('ffmpeg'), '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '1', str(audio)])
    command([binary('ffmpeg'), '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=25', '-i', str(audio), '-t', '1', '-c:v', 'libx264', '-c:a', 'aac', str(video)])
    return audio.read_bytes(), video.read_bytes()


def test_real_media_conversion_removes_video_audio(media, tmp_path):
    parts = media_content([media[0]], [media[1]])
    assert parts[0]['text'].startswith('<Audio 1>') and parts[2]['text'].startswith('<Video 1>')
    raw = base64.b64decode(parts[1]['input_audio']['data'].split(',', 1)[1])
    with wave.open(io.BytesIO(raw)) as audio:
        assert audio.getframerate() == 16000 and audio.getnchannels() == 1
        assert audio.getnframes() == 16000
    path = tmp_path / 'converted.mp4'
    path.write_bytes(base64.b64decode(parts[3]['video_url']['url'].split(',', 1)[1]))
    assert {s['codec_type'] for s in probe(path)['streams']} == {'video'}


def test_worker_multimodal_reaches_actual_request(tmp_path, monkeypatch, media):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    audio = store.add_asset(pid, media[0], 'a.wav')
    video = store.add_asset(pid, media[1], 'v.mp4')
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 8, 'referenceIds': [audio['id'], video['id']]})
    store.save_canvas(pid, canvas, canvas['version'])
    calls = []
    def post(client, url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': REWRITE}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    run = worker.submit(pid, ['script'])
    while worker.tick():
        pass
    tasks = store.run(run['id'])['tasks']
    assert all(t['status'] == 'completed' for t in tasks), tasks
    assert len(calls) == 1
    content = calls[0]['messages'][1]['content']
    assert [p['type'] for p in content] == ['text', 'text', 'video_url']
    assert content[1]['text'].startswith('<Video 1>')
    assert 'action causality' in calls[0]['messages'][0]['content']
    assert next(t for t in tasks if t['node_id'] == 'script')['output']['seconds'] == 8


@pytest.mark.parametrize('audios,videos', [([b'a'] * 4, []), ([], [b'v'] * 4), ([b''], []), ([], [b'x' * (20 * 1024 * 1024 + 1)])])
def test_invalid_media_limits(audios, videos):
    with pytest.raises(ValueError):
        validate_expansion_inputs(8, [], audios, videos)


def test_duration_and_type_errors(monkeypatch):
    monkeypatch.setattr('app.expansion_media.probe', lambda path: {'format': {'duration': '121'}, 'streams': [{'codec_type': 'audio'}]})
    with pytest.raises(ValueError, match='120'):
        media_content([b'a'], [])
    with pytest.raises(ValueError, match='类型'):
        media_content([], [b'a'])


def test_model_rejection_explains_compatibility(tmp_path, monkeypatch, media):
    _, _, worker = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(httpx.Client, 'post', lambda client, url, **kwargs: httpx.Response(400, request=httpx.Request('POST', url)))
    with pytest.raises(ProviderError, match='多模态模型'):
        TextProvider(settings=worker.settings).generate('prompt.video_expand', 'scene', videos=[media[1]])
    inputs = DEFINITIONS['prompt.video_expand']['inputs']
    assert sum(t == 'image' for t in inputs.values()) == 9
    assert sum(t == 'audio' for t in inputs.values()) == sum(t == 'video' for t in inputs.values()) == 3


def test_expansion_ignores_legacy_audio_dependencies_and_snapshots(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 8})
    canvas['nodes'].append({'id': 'voice', 'type': 'studio', 'position': {'x': 0, 'y': 0},
                            'data': {'kind': 'audio.tts', 'config': {'prompt': 'must not run'}}})
    canvas['edges'].append({'id': 'legacy-audio', 'source': 'voice', 'sourceHandle': 'audio',
                            'target': 'script', 'targetHandle': 'audio', 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    assert 'voice' not in [task['node_id'] for task in store.run(run['id'])['tasks']]
    task = next(task for task in store.run(run['id'])['tasks'] if task['node_id'] == 'script')
    task['snapshot']['links'] = [{'source': 'missing', 'port': 'audio'}]
    task['snapshot']['references'] = [{'id': 'missing-asset', 'mime': 'audio/wav'}]
    task['snapshot']['config']['prompt'] = 'scene'
    _, inputs, _ = worker.inputs(task, {})
    assert 'audio' not in inputs
