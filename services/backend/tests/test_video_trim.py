import pytest

from app.video_trim import trim_video
from app.exporter import binary, command, probe
from app.costs import quote_snapshot
from app.credentials import Settings
from app.store import Store
from app.worker import Worker


@pytest.fixture
def videos(tmp_path):
    result = []
    for sound in [False, True]:
        path = tmp_path / f'source-{sound}.mp4'
        args = [binary('ffmpeg'), '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=25']
        if sound:
            args += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-c:a', 'aac']
        command(args + ['-t', '3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)])
        result.append(path.read_bytes())
    return result


def test_actual_video_interval_and_audio(videos, tmp_path):
    for sound, source in enumerate(videos):
        for end in [1.76, None]:
            config = {'trimStart': .52, 'trimEnd': end}
            output = tmp_path / 'trim.mp4'
            output.write_bytes(trim_video([source], config))
            info = probe(output)
            assert float(info['format']['duration']) == pytest.approx((end or 3) - .52, abs=.06)
            assert any(s['codec_type'] == 'audio' for s in info['streams']) == bool(sound)
            assert next(s for s in info['streams'] if s['codec_type'] == 'video')['codec_name'] == 'h264'
        assert videos[sound] == source


@pytest.mark.parametrize('config', [{'trimStart': -1}, {'trimEnd': 0}, {'trimStart': 1, 'trimEnd': .5},
    {'trimStart': True}, {'trimStart': float('nan')}, {'trimEnd': float('inf')}, {'trimEnd': '2'}])
def test_invalid_range(config):
    with pytest.raises(ValueError):
        trim_video([b'unread'], config)


def test_bounds_and_missing_inputs(videos):
    for config in [{'trimStart': 3}, {'trimEnd': 4}]:
        with pytest.raises(ValueError, match='超出'):
            trim_video([videos[0]], config)
    for inputs in [[], videos]:
        with pytest.raises(ValueError, match='一个视频'):
            trim_video(inputs, {})


def test_audio_only_rejected(monkeypatch):
    monkeypatch.setattr('app.video_trim.probe', lambda path: {'streams': [{'codec_type': 'audio'}]})
    with pytest.raises(ValueError, match='不含视频'):
        trim_video([b'audio'], {})


def test_local_execution_cache_and_changed_range(tmp_path, monkeypatch, videos):
    store = Store(tmp_path / 'data')
    pid = store.create_project('video trim')['id']
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    monkeypatch.setattr(worker.provider, 'submit', lambda *args: pytest.fail('cloud must not be called'))
    asset = store.add_asset(pid, videos[1], 'source.mp4')
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': n, 'type': 'studio', 'position': {'x': x, 'y': 0}, 'data': {'kind': kind, 'config': config}}
        for n, x, kind, config in [('source', 0, 'asset.video', {'assetId': asset['id']}), ('trim', 300, 'video.trim', {'trimStart': .5, 'trimEnd': 1.5})]]
    canvas['edges'] = [{'id': 'video', 'source': 'source', 'target': 'trim', 'sourceHandle': 'video', 'targetHandle': 'video'}]
    store.save_canvas(pid, canvas, canvas['version'])
    def run(force=False):
        job = worker.submit(pid, ['trim'], force=force)
        while worker.tick():
            pass
        tasks = store.run(job['id'])['tasks']
        assert all(t['status'] == 'completed' for t in tasks), tasks
        task = next(t for t in tasks if t['node_id'] == 'trim')
        assert not task['submitted'] and not task['external_id']
        assert Store.queue_name(task['snapshot']) == 'local'
        return task
    original = run()
    assert run()['reused']
    assert not run(True)['reused']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data']['config']['trimEnd'] = 2.5
    store.save_canvas(pid, canvas, canvas['version'])
    changed = run()
    assert not changed['reused'] and changed['output'] != original['output']
    output = store.asset_path(changed['output']['assets'][0])
    assert float(probe(output)['format']['duration']) == pytest.approx(2, abs=.06)
    assert store.asset_path(asset['id']).read_bytes() == videos[1]
    quote = quote_snapshot({'kind': 'video.trim', 'config': {}}, {})
    assert quote['basis'] == 'local' and quote['amount'] == '0.000000'
