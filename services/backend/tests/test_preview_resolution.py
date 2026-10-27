import copy
import json

import pytest

from app.exporter import binary, command, export_timeline, probe
from app.store import Store
from app.graph import snapshot_hash
from app.timeline import normalize_timeline
from test_settings_api import client


@pytest.mark.parametrize('width,height,mode,expected', [
    (1280, 720, 'source', (1280, 720)),
    (720, 1280, 'source', (720, 1280)),
    (64, 64, 'source', (64, 64)),
    (320, 180, 'timeline', (1280, 720)),
])
def test_preview_keeps_final_render_resolution(tmp_path, width, height, mode, expected):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required for real preview resolution regression')
    source = tmp_path / 'source.mp4'
    command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i',
             f'testsrc2=size={width}x{height}:rate=24:duration=0.5',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)])
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Full resolution preview')['id']
    asset = store.add_asset(pid, source.read_bytes(), source.name)
    timeline = {'width': 1280, 'height': 720, 'fps': 24, 'exportMode': mode,
                'clips': [{'assetId': asset['id'], 'durationMs': 500, 'approved': True}]}
    original = copy.deepcopy(timeline)
    renders = []
    for preview in (True, False):
        result = export_timeline(store, pid, timeline, 'preview' if preview else 'final', preview=preview)
        output = store.project_dir(pid) / result['path']
        stream = next(s for s in probe(output)['streams'] if s['codec_type'] == 'video')
        assert (stream['width'], stream['height']) == expected
        assert stream['r_frame_rate'] == '24/1'
        renders.append(json.loads(output.with_suffix('.manifest.json').read_text(encoding='utf-8'))['render'])
    assert renders[0] == renders[1]
    assert timeline == original


@pytest.mark.parametrize('renderer', [None, 'full-resolution-v1'])
def test_preview_invalidates_legacy_cache_and_reuses_current_cache(client, monkeypatch, renderer):
    from app import main
    monkeypatch.setattr(main, 'binary', lambda name: name)
    monkeypatch.setattr(main, 'validate_timeline', lambda *_: [])
    # 本用例只验证任务去重，不运行媒体线程；实际媒体由上面的真实视频用例覆盖。
    monkeypatch.setattr(main.ThreadPoolExecutor, 'submit', lambda *_: None)
    store = client.app.state.store
    pid = store.create_project('Preview cache')['id']
    timeline = store.put_document(pid, 'timeline', {'clips': [
        {'assetId': 'cache-fixture', 'durationMs': 1000, 'approved': True}]})
    old_hash = snapshot_hash({k: v for k, v in normalize_timeline(timeline).items() if k != 'version'})
    if renderer:
        old_hash = snapshot_hash({'timelineHash': old_hash, 'previewRenderer': renderer})
    old_id = pid + '_old'
    store.put_document(pid, 'export:' + old_id, {
        'id': old_id, 'preview': True, 'inputHash': old_hash, 'status': 'queued'})
    first = client.post(f'/api/v1/projects/{pid}/preview')
    assert first.status_code == 202
    assert first.json()['id'] != old_id
    second = client.post(f'/api/v1/projects/{pid}/preview')
    assert second.status_code == 202
    assert second.json()['id'] == first.json()['id']
