"""用真实高频画面检查二次导出损失，避免纯色素材掩盖细节损失。"""
import subprocess
import json

import pytest

from app.exporter import binary, command, export_timeline, probe
from app.store import Store


@pytest.mark.parametrize('encoding', ['compatible', 'lossless'])
def test_export_preserves_fine_details(tmp_path, encoding):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required for export quality regression')
    source = tmp_path / 'detail.mp4'
    command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i',
             'testsrc2=size=640x360:rate=24:duration=1',
             '-c:v', 'libx264', '-crf', '0', '-pix_fmt', 'yuv420p', str(source)])
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Export quality')['id']
    asset = store.add_asset(pid, source.read_bytes(), source.name)
    timeline = {'width': 640, 'height': 360, 'fps': 24, 'clips': [
        {'assetId': asset['id'], 'durationMs': 1000, 'approved': True}], 'audio': [], 'subtitles': []}
    if encoding == 'lossless':
        timeline['videoEncoding'] = 'lossless'
    result = export_timeline(store, pid, timeline, 'detail')
    output = store.project_dir(pid) / result['path']
    stream = next(s for s in probe(output)['streams'] if s['codec_type'] == 'video')
    assert (stream['width'], stream['height'], stream['r_frame_rate']) == (640, 360, '24/1')
    if encoding == 'compatible':
        assert stream['profile'] == 'High'
        assert stream['pix_fmt'] == 'yuv420p'
        assert stream['codec_tag_string'] == 'avc1'
        assert any(s['codec_name'] == 'aac' for s in probe(output)['streams'])
        manifest = json.loads(output.with_suffix('.manifest.json').read_text(encoding='utf-8'))
        assert manifest['videoEncoding'] == 'h264-compatible'
    def decoded(path):
        return subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-map', '0:v:0',
                               '-pix_fmt', 'yuv420p', '-f', 'rawvideo', '-'],
                              capture_output=True, check=True).stdout
    original, exported = decoded(source), decoded(output)
    assert len(original) == 24 * 640 * 360 * 3 // 2
    assert len(exported) == len(original)
    if encoding == 'lossless':
        assert exported == original, '无损导出必须逐帧保留全部亮度和色度样本'
    else:
        # 高质量兼容编码不应重现白屏，也不应以强压缩换取兼容。
        mse = sum((a - b) ** 2 for a, b in zip(original, exported)) / len(original)
        assert mse < 2


def test_invalid_video_encoding_is_rejected():
    from app.timeline import normalize_timeline
    with pytest.raises(ValueError, match='编码'):
        normalize_timeline({'clips': [], 'videoEncoding': 'invalid'}, allow_empty=True)


@pytest.mark.parametrize('settings', [
    {'transform': {'opacity': 0.5}}, {'fadeInMs': 1000}, {'fadeOutMs': 1000},
])
def test_transparency_and_fades_keep_expected_brightness(tmp_path, settings):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required for alpha regression')
    source = tmp_path / 'white.mp4'
    command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i',
             'color=white:size=128x128:rate=24:duration=1', str(source)])
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Alpha regression')['id']
    asset = store.add_asset(pid, source.read_bytes(), source.name)
    result = export_timeline(store, pid, {'width': 128, 'height': 128, 'fps': 24, 'exportMode': 'timeline',
        'clips': [{'assetId': asset['id'], 'durationMs': 1000, 'approved': True, **settings}]}, 'alpha')
    output = store.project_dir(pid) / result['path']
    pixels = subprocess.run([ffmpeg, '-v', 'error', '-ss', '0.5', '-i', str(output),
                             '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
                            capture_output=True, check=True).stdout
    assert len(pixels) == 128 * 128 * 3
    assert all(115 <= value <= 140 for value in pixels[:3]), pixels[:3]
