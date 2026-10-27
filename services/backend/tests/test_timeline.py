import array
import math
import os
import subprocess

import pytest

from app.timeline import normalize_timeline, filter_graph
from app.exporter import binary, command, export_timeline, probe
from app.store import Store


def clip(**values):
    return {'id': 'clip', 'assetId': 'fixture', 'durationMs': 1000, 'inMs': 0, 'approved': True, **values}


def test_legacy_sequential_timeline_and_explicit_overlay():
    result = normalize_timeline({'clips': [clip(id='a'), clip(id='b'), clip(id='c', track='V2', startMs=250)], 'audio': [], 'subtitles': []})
    assert [c['startMs'] for c in result['clips']] == [0, 1000, 250]
    assert result['durationMs'] == 2000
    assert result['clips'][2]['track'] == 'V2'


@pytest.mark.parametrize('values', [{'inMs': -1}, {'gain': float('nan')}, {'durationMs': float('inf')},
    {'startMs': 'oops'}, {'track': 'V99'}, {'fadeInMs': 2000}, {'transform': {'width': -1}}, {'muted': 'true'}])
def test_invalid_editing_parameters_rejected(values):
    with pytest.raises(ValueError):
        normalize_timeline({'clips': [clip(**values)]})


def test_audio_tracks_and_filtergraph_preserve_editing():
    timeline = normalize_timeline({'clips': [clip(inMs=250, gain=0.2)], 'audio': [clip(id='voice', track='A1', inMs=100, startMs=300, durationMs=500, gain=0.5, fadeInMs=100)], 'subtitles': []})
    graph = filter_graph(timeline, [True])
    assert 'trim=start=0.25' in graph
    assert 'volume=0.2' in graph
    assert 'adelay=300|300' in graph
    assert 'afade=t=in' in graph
    assert 'alimiter=' in graph


def test_empty_timeline_can_be_saved_but_not_exported():
    assert normalize_timeline({'clips': []}, allow_empty=True)['durationMs'] == 0
    with pytest.raises(ValueError):
        normalize_timeline({'clips': []})


def test_real_multitrack_overlay_audio_and_preview(tmp_path):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except ValueError:
        pytest.skip('FFmpeg required for real multi-track rendering')
    blue, red, audio = tmp_path / 'blue.mp4', tmp_path / 'red.mp4', tmp_path / 'voice.wav'
    for target, color in ((blue, 'blue'), (red, 'red')):
        command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color=c={color}:s=128x128:r=30:d=2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(target)])
    command([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', str(audio)])
    store = Store(tmp_path / 'projects')
    pid = store.create_project('Multi-track')['id']
    assets = [store.add_asset(pid, p.read_bytes(), p.name) for p in (blue, red, audio)]
    timeline = {'width': 128, 'height': 128, 'fps': 30, 'exportMode': 'timeline',
        'clips': [clip(id='blue', assetId=assets[0]['id'], durationMs=2000, muted=True),
                  clip(id='red', assetId=assets[1]['id'], startMs=1000, track='V2', inMs=500,
                       transform={'x': 32, 'y': 32, 'width': 64, 'height': 64}, muted=True)],
        'audio': [clip(id='voice', assetId=assets[2]['id'], track='A2', startMs=500, durationMs=1500, gain=0.1)],
        'subtitles': []}
    result = export_timeline(store, pid, timeline, 'multitrack')
    output = store.project_dir(pid) / result['path']
    assert abs(float(probe(output)['format']['duration']) - 2) <= 1 / 30
    pixels = subprocess.run([ffmpeg, '-v', 'error', '-ss', '1.5', '-i', str(output), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    corner = pixels[:3]
    center = pixels[(64 * 128 + 64) * 3:(64 * 128 + 64) * 3 + 3]
    assert corner[2] > 200 and corner[0] < 30
    assert center[0] > 200 and center[2] < 30
    raw = subprocess.run([ffmpeg, '-v', 'error', '-i', str(output), '-vn', '-ac', '1', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    samples = array.array('f', raw)
    quiet = math.sqrt(sum(v*v for v in samples[:12000]) / 12000)
    sound = math.sqrt(sum(v*v for v in samples[48000:60000]) / 12000)
    assert quiet < 0.001 and sound > 0.001
    preview = export_timeline(store, pid, timeline, 'preview', preview=True)
    assert preview['preview'] is True
    assert preview['durationMs'] == 2000
