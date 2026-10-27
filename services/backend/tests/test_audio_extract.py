import wave
import io

import pytest

from app.audio_extract import extract_audio
from app.costs import quote_snapshot
from app.credentials import Settings
from app.exporter import binary, command
from app.graph import DEFINITIONS
from app.store import Store
from app.worker import Worker


@pytest.fixture
def videos(tmp_path):
    result = []
    for sound in [False, True]:
        path = tmp_path / f'{sound}.mp4'
        args = [binary('ffmpeg'), '-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=white:s=64x64:r=25']
        if sound:
            args += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-c:a', 'aac']
        command(args + ['-t', '1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)])
        result.append(path.read_bytes())
    return result


def test_real_audio_extraction(videos):
    original = videos[1]
    data = extract_audio([original])
    with wave.open(io.BytesIO(data)) as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getnframes() / audio.getframerate() == pytest.approx(1, abs=.05)
    assert videos[1] == original


def test_silent_video_error(videos):
    with pytest.raises(ValueError, match='不含音轨'):
        extract_audio([videos[0]])


@pytest.mark.parametrize('videos', [[], [b'a', b'b']])
def test_requires_one_video(videos):
    with pytest.raises(ValueError, match='一个视频'):
        extract_audio(videos)


def test_local_execution_cache_and_force(tmp_path, monkeypatch, videos):
    store = Store(tmp_path / 'data')
    project = store.create_project('提取测试')
    pid = project['id']
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    monkeypatch.setattr(worker.provider, 'submit', lambda *args: pytest.fail('must not call provider'))
    asset = store.add_asset(pid, videos[1], 'input.mp4')
    c = store.canvas(pid)
    c['nodes'] = [{'id': id, 'type': 'studio', 'position': {'x': x, 'y': 0}, 'data': {'kind': kind, 'config': config}}
                  for id, x, kind, config in [('source', 0, 'asset.video', {'assetId': asset['id']}), ('extract', 300, 'audio.extract', {})]]
    c['edges'] = [{'id': 'video', 'source': 'source', 'target': 'extract', 'sourceHandle': 'video', 'targetHandle': 'video'}]
    store.save_canvas(pid, c, c['version'])
    assert not project['settings'].get('cloudEnabled')
    def run(force=False):
        job = worker.submit(pid, ['extract'], force=force)
        while worker.tick():
            pass
        tasks = store.run(job['id'])['tasks']
        assert all(t['status'] == 'completed' for t in tasks)
        task = next(t for t in tasks if t['node_id'] == 'extract')
        assert not task['submitted'] and not task['external_id']
        assert Store.queue_name(task['snapshot']) == 'local'
        return task
    first = run()
    output = store.asset(first['output']['assets'][0])
    assert output['mime'].startswith('audio/') and output['nodeId'] == 'extract'
    cached = run()
    assert cached['reused'] and cached['output'] == first['output']
    fresh = run(True)
    assert not fresh['reused']
    assert fresh['output']['assets'] != first['output']['assets']
    assert DEFINITIONS['audio.extract']['inputs'] == {'video': 'video'}
    quote = quote_snapshot({'kind': 'audio.extract', 'config': {}}, {})
    assert quote['basis'] == 'local' and quote['amount'] == '0.000000'
