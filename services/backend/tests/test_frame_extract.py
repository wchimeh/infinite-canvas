import io

import pytest
from PIL import Image

from app.frame_extract import extract_frame
from app.exporter import binary, command
from app.costs import quote_snapshot
from app.credentials import Settings
from app.store import Store
from app.worker import Worker


@pytest.fixture
def video(tmp_path):
    path = tmp_path / 'colors.mp4'
    command([binary('ffmpeg'), '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=red:s=128x72:r=10:d=1',
             '-f', 'lavfi', '-i', 'color=blue:s=128x72:r=10:d=1', '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[v]',
             '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)])
    return path.read_bytes()


@pytest.mark.parametrize('time,channel', [(0, 0), (.99, 0), (1, 2), (1.99, 2), (2, 2)])
def test_current_frame_and_resolution(video, time, channel):
    image = Image.open(io.BytesIO(extract_frame([video], {'frameTime': time})))
    assert image.format == 'PNG' and image.size == (128, 72)
    pixel = image.convert('RGB').getpixel((64, 36))
    assert pixel[channel] > 240 and sum(pixel) < 270


@pytest.mark.parametrize('time', [-1, True, '1', None, float('nan'), float('inf')])
def test_invalid_time(time):
    with pytest.raises(ValueError, match='时间'):
        extract_frame([b'video'], {'frameTime': time})


def test_missing_multiple_and_out_of_bounds(video):
    for inputs in [[], [video, video]]:
        with pytest.raises(ValueError, match='一个视频'):
            extract_frame(inputs, {})
    with pytest.raises(ValueError, match='超出'):
        extract_frame([video], {'frameTime': 2.1})


def test_audio_only_rejected(monkeypatch):
    monkeypatch.setattr('app.frame_extract.probe', lambda _: {'streams': [{'codec_type': 'audio'}]})
    with pytest.raises(ValueError, match='视频画面'):
        extract_frame([b'audio'], {})


def test_local_worker_and_cache(tmp_path, monkeypatch, video):
    store = Store(tmp_path / 'data')
    pid = store.create_project('frame')['id']
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    monkeypatch.setattr(worker.provider, 'submit', lambda *args: pytest.fail('must not call cloud'))
    asset = store.add_asset(pid, video, 'source.mp4')
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': n, 'position': {'x': x, 'y': 0}, 'data': {'kind': kind, 'config': config}}
        for n, x, kind, config in [('source', 0, 'asset.video', {'assetId': asset['id']}), ('frame', 300, 'frame.extract', {'frameTime': .99})]]
    canvas['edges'] = [{'id': 'video', 'source': 'source', 'target': 'frame', 'sourceHandle': 'video', 'targetHandle': 'video'}]
    store.save_canvas(pid, canvas, canvas['version'])
    def run():
        job = worker.submit(pid, ['frame'])
        while worker.tick():
            pass
        task = next(t for t in store.run(job['id'])['tasks'] if t['node_id'] == 'frame')
        assert task['status'] == 'completed', task
        assert not task['submitted'] and not task['external_id']
        assert Store.queue_name(task['snapshot']) == 'local'
        assert store.asset(task['output']['assets'][0])['mime'] == 'image/png'
        return task
    first = run()
    assert run()['reused']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data']['config']['frameTime'] = 1.5
    store.save_canvas(pid, canvas, canvas['version'])
    second = run()
    assert not second['reused'] and second['output'] != first['output']
    assert store.asset_path(asset['id']).read_bytes() == video
    quote = quote_snapshot({'kind': 'frame.extract', 'config': {}}, {})
    assert quote['basis'] == 'local' and quote['amount'] == '0.000000'
