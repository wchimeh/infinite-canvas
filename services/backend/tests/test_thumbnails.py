import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.credentials import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / 'data', token='thumbnail-test', start_worker=False,
                     settings=Settings(tmp_path / 'config'))
    with TestClient(app, headers={'Authorization': 'Bearer thumbnail-test'}) as client:
        yield client


def thumbnail(client, image, extension, **options):
    source = io.BytesIO()
    image.save(source, **options)
    raw = source.getvalue()
    project = client.app.state.store.create_project('Thumbnail test')
    asset = client.app.state.store.add_asset(project['id'], raw, 'source.' + extension)
    result = client.get(f'/api/v1/assets/{asset["id"]}/thumbnail')
    assert result.status_code == 200
    assert result.headers['content-type'] == 'image/jpeg'
    assert client.get(f'/api/v1/assets/{asset["id"]}/content').content == raw
    return Image.open(io.BytesIO(result.content))


@pytest.mark.parametrize('orientation', [6, 8])
def test_thumbnail_applies_photo_orientation(client, orientation):
    image = Image.new('RGB', (80, 40), 'blue')
    image.paste('red', (0, 0, 40, 40))
    exif = Image.Exif()
    exif[274] = orientation
    result = thumbnail(client, image, 'jpg', format='JPEG', exif=exif)
    assert result.size == (40, 80)
    top = result.getpixel((20, 10))
    bottom = result.getpixel((20, 70))
    assert (top[0] > top[2]) == (orientation == 6)
    assert (bottom[0] > bottom[2]) == (orientation == 8)


@pytest.mark.parametrize('mode', ['RGBA', 'P'])
def test_thumbnail_composites_transparency_on_white(client, mode):
    image = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (20, 20, 60, 60))
    if mode == 'P':
        image = image.convert('P', palette=Image.Palette.ADAPTIVE)
    result = thumbnail(client, image, 'png', format='PNG')
    assert min(result.getpixel((5, 5))) > 245
    red = result.getpixel((40, 40))
    assert red[0] > 240 and max(red[1:]) < 15


def test_thumbnail_preserves_aspect_ratio_and_limits_size(client):
    result = thumbnail(client, Image.new('RGB', (1200, 600), 'white'), 'png', format='PNG')
    assert result.size == (480, 240)


@pytest.mark.parametrize('size,expected', [('960x540', (480, 270)), ('540x960', (270, 480))])
def test_video_thumbnail_first_frame_cached_and_source_unchanged(client, tmp_path, monkeypatch, size, expected):
    from app.exporter import binary, command
    path = tmp_path / 'video.mp4'
    command([binary('ffmpeg'), '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=red:s={size}:r=5:d=0.4',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)])
    raw = path.read_bytes()
    project = client.app.state.store.create_project('Video thumbnail')
    asset = client.app.state.store.add_asset(project['id'], raw, 'video.mp4')
    response = client.get(f'/api/v1/assets/{asset["id"]}/thumbnail')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert response.headers['cache-control'] == 'private, max-age=3600'
    with Image.open(io.BytesIO(response.content)) as image:
        assert image.size == expected
        pixel = image.convert('RGB').getpixel((10, 10))
        assert pixel[0] > 220 and pixel[1] < 30 and pixel[2] < 30
    monkeypatch.setattr('app.video_thumbnail.binary', lambda _: pytest.fail('缓存命中不应再次启动 FFmpeg'))
    assert client.get(f'/api/v1/assets/{asset["id"]}/thumbnail').content == response.content
    assert client.get(f'/api/v1/assets/{asset["id"]}/content').content == raw


def test_invalid_video_and_audio_thumbnail_fail_cleanly(client):
    project = client.app.state.store.create_project('Invalid thumbnail')
    for name in ['broken.mp4', 'audio.wav']:
        asset = client.app.state.store.add_asset(project['id'], b'invalid media', name)
        response = client.get(f'/api/v1/assets/{asset["id"]}/thumbnail')
        assert response.status_code == 400
        assert response.json()['message']


def test_video_thumbnail_missing_decoder_and_timeout(tmp_path, monkeypatch):
    import subprocess
    from app.video_thumbnail import video_thumbnail
    path = tmp_path / 'video.mp4'
    path.write_bytes(b'video')
    def missing(_):
        raise ValueError('未找到 ffmpeg')
    monkeypatch.setattr('app.video_thumbnail.binary', missing)
    with pytest.raises(ValueError, match='ffmpeg'):
        video_thumbnail(path)
    monkeypatch.setattr('app.video_thumbnail.binary', lambda _: 'ffmpeg')
    def timeout(*args, **kwargs):
        assert kwargs['timeout'] == 15
        raise subprocess.TimeoutExpired('ffmpeg', 15)
    monkeypatch.setattr('app.video_thumbnail.subprocess.run', timeout)
    with pytest.raises(ValueError, match='超时'):
        video_thumbnail(path)


@pytest.mark.parametrize('same_file', [False, True])
def test_video_thumbnail_limits_concurrency_and_coalesces_requests(tmp_path, monkeypatch, same_file):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import time
    from types import SimpleNamespace
    from app.video_thumbnail import video_thumbnail
    paths = [tmp_path / f'clip-{i}.mp4' for i in range(4)]
    for path in paths:
        path.write_bytes(b'video')
    lock = threading.Lock()
    active = peak = calls = 0
    def decode(args, **kwargs):
        nonlocal active, peak, calls
        with lock:
            active += 1
            peak = max(peak, active)
            calls += 1
        time.sleep(.03)
        with lock:
            active -= 1
        return SimpleNamespace(returncode=0, stdout=b'jpeg')
    monkeypatch.setattr('app.video_thumbnail.binary', lambda _: 'ffmpeg')
    monkeypatch.setattr('app.video_thumbnail.subprocess.run', decode)
    barrier = threading.Barrier(4)
    def request(i):
        barrier.wait()
        return video_thumbnail(paths[0 if same_file else i])
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(request, range(4))) == [b'jpeg'] * 4
    assert peak == 1
    assert calls == (1 if same_file else 4)


def test_thumbnail_decoder_thread_limits_and_warm_cache_during_cold_request(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from types import SimpleNamespace
    from app.video_thumbnail import video_thumbnail
    warm, cold = tmp_path / 'warm.mp4', tmp_path / 'cold.mp4'
    warm.write_bytes(b'warm'); cold.write_bytes(b'cold')
    started, finish = threading.Event(), threading.Event()
    def decode(args, **kwargs):
        assert args.count('-threads') == 2
        assert args[args.index('-threads') + 1] == '1'
        assert args[args.index('-filter_threads') + 1] == '1'
        if str(cold.resolve()) in args:
            started.set()
            assert finish.wait(3)
        return SimpleNamespace(returncode=0, stdout=b'jpeg')
    monkeypatch.setattr('app.video_thumbnail.binary', lambda _: 'ffmpeg')
    monkeypatch.setattr('app.video_thumbnail.subprocess.run', decode)
    video_thumbnail(warm)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(video_thumbnail, cold)
        try:
            assert started.wait(2)
            assert pool.submit(video_thumbnail, warm).result(timeout=.5) == b'jpeg'
        finally:
            finish.set()
        assert future.result() == b'jpeg'
