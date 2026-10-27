import copy
import json
import subprocess

import pytest

from app.timeline import normalize_timeline
from app.lossless_timeline import preserve_source_timeline
from app.exporter import binary, command, export_timeline, probe
from app.store import Store


def fixture():
    timeline = normalize_timeline({'clips': [
        {'id': str(i), 'assetId': str(i), 'durationMs': 1000, 'approved': True} for i in range(2)]})
    streams = [{'width': w, 'height': h, 'pix_fmt': 'yuv420p', 'avg_frame_rate': '24/1',
                'r_frame_rate': '24/1'} for w, h in ((640, 360), (320, 240))]
    return timeline, streams


def test_native_dimensions_rate_and_proportional_resize():
    timeline, streams = fixture()
    before = copy.deepcopy(timeline)
    result = preserve_source_timeline(timeline, streams)
    assert (result['width'], result['height'], result['fps']) == (640, 360, 24)
    assert result['clips'][1]['transform'] == {
        'width': 640, 'height': 360, 'x': 0, 'y': 0, 'fit': 'contain', 'opacity': 1}
    assert timeline == before


@pytest.mark.parametrize('large,small', [((640, 360), (320, 180)), ((360, 640), (180, 320)), ((640, 640), (320, 320))])
def test_same_aspect_clips_fill_canvas(large, small):
    timeline, streams = fixture()
    for stream, (width, height) in zip(streams, (large, small)):
        stream.update(width=width, height=height)
    result = preserve_source_timeline(timeline, streams)
    for clip in result['clips']:
        assert (clip['transform']['width'], clip['transform']['height']) == large
        assert (clip['transform']['x'], clip['transform']['y']) == (0, 0)


def test_real_smaller_same_aspect_clip_has_no_black_frame(tmp_path):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required')
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Resize regression')['id']
    clips = []
    for index, size in enumerate(('640x360', '320x180')):
        path = tmp_path / f'{index}.mp4'
        command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color=red:s={size}:r=24:d=1', str(path)])
        asset = store.add_asset(pid, path.read_bytes(), path.name)
        clips.append({'assetId': asset['id'], 'durationMs': 1000, 'approved': True})
    result = export_timeline(store, pid, {'clips': clips}, 'resize')
    pixels = subprocess.run([ffmpeg, '-v', 'error', '-ss', '1.5', '-i', str(store.project_dir(pid) / result['path']),
                             '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    assert len(pixels) == 640 * 360 * 3
    for x, y in ((0, 0), (639, 0), (0, 359), (639, 359), (320, 180)):
        offset = (y * 640 + x) * 3
        assert pixels[offset] > 220, f'Unexpected black border at {x},{y}'


@pytest.mark.parametrize('field,value', [
    ('pix_fmt', 'yuv420p10le'), ('pix_fmt', 'yuv444p'), ('color_range', 'pc'),
    ('color_transfer', 'smpte2084'), ('avg_frame_rate', '30/1'),
    ('r_frame_rate', '30/1'), ('width', 639),
])
def test_unsupported_sources_never_silently_lose_information(field, value):
    timeline, streams = fixture()
    streams[1][field] = value
    with pytest.raises(ValueError, match='原片'):
        preserve_source_timeline(timeline, streams)


@pytest.mark.parametrize('change', [
    {'startMs': 0}, {'track': 'V2'}, {'fadeInMs': 100},
    {'transform': {'width': 128, 'height': 128}},
])
def test_composition_requires_explicit_mode(change):
    timeline, streams = fixture()
    timeline['clips'][1].update(change)
    with pytest.raises(ValueError, match='按时间线合成'):
        preserve_source_timeline(timeline, streams)


def test_real_resized_clips_match_reference_composition(tmp_path):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required for native export regression')
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Native lossless')['id']
    clips, sources = [], []
    # 不同宽高比验证只保留必要留边；原项目默认为竖屏 30 fps。
    for index, (width, height) in enumerate(((640, 360), (318, 238))):
        source = tmp_path / f'{index}.mp4'
        command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i',
                 f'testsrc2=size={width}x{height}:rate=24:duration=1',
                 '-c:v', 'libx264', '-qp', '0', str(source)])
        sources.append(source)
        asset = store.add_asset(pid, source.read_bytes(), source.name)
        clips.append({'assetId': asset['id'], 'durationMs': 1000, 'approved': True})
    result = export_timeline(store, pid, {'clips': clips, 'videoEncoding': 'lossless'}, 'native')
    output = store.project_dir(pid) / result['path']
    stream = next(s for s in probe(output)['streams'] if s['codec_type'] == 'video')
    assert (stream['width'], stream['height'], stream['r_frame_rate']) == (640, 360, '24/1')
    for index in range(2):
        def pixels(path, filters):
            return subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-vf', filters,
                                   '-pix_fmt', 'yuv420p', '-f', 'rawvideo', '-'],
                                  capture_output=True, check=True).stdout
        reference = pixels(sources[index],
            'scale=640:360:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,pad=640:360:(ow-iw)/2:(oh-ih)/2')
        exported = pixels(output, f'trim=start={index}:duration=1,setpts=PTS-STARTPTS')
        assert len(reference) == 24 * 640 * 360 * 3 // 2
        assert exported == reference
    manifest = json.loads(output.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    assert manifest['videoEncoding'] == 'h264-lossless'
    assert manifest['exportMode'] == 'source'
    assert manifest['timeline']['width'] == 1080
    assert manifest['render']['width'] == 640


def test_actual_variable_frame_timing_is_rejected(monkeypatch):
    from app import exporter
    monkeypatch.setattr(exporter, 'binary', lambda _: 'ffprobe')
    monkeypatch.setattr(exporter, 'command', lambda _: json.dumps({'frames': [
        {'best_effort_timestamp_time': value} for value in ('0.000000', '0.041667', '0.125000')]}))
    with pytest.raises(ValueError, match='可变帧率'):
        exporter.validate_source_frame_timing('fixture.mp4', 24)
