import io
import struct
import wave

import pytest

from app.audio_trim import trim_audio
from app.costs import quote_snapshot
from app.credentials import Settings
from app.graph import DEFINITIONS
from app.store import Store
from app.worker import Worker


@pytest.fixture
def audio():
    stream = io.BytesIO()
    frames = b''.join(struct.pack('<h', i % 16000 - 8000) for i in range(32000))
    with wave.open(stream, 'wb') as out:
        out.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        out.writeframes(frames)
    return stream.getvalue(), frames


def test_exact_audio_segment_and_remainder(audio):
    source, frames = audio
    for config, start, end in [({'trimStart': 0.25, 'trimEnd': 1.75}, 2000, 14000), ({'trimStart': 2.5}, 20000, 32000), ({}, 0, 32000)]:
        result = trim_audio([source], config)
        with wave.open(io.BytesIO(result)) as output:
            assert output.getframerate() == 8000
            assert output.getnframes() == end - start
            assert output.readframes(output.getnframes()) == frames[start * 2:end * 2]
    assert audio[0] == source


@pytest.mark.parametrize('config', [{'trimStart': -1}, {'trimStart': True}, {'trimStart': float('nan')},
    {'trimEnd': float('inf')}, {'trimEnd': '2'}, {'trimStart': 2, 'trimEnd': 1},
    {'trimStart': 2, 'trimEnd': 2}, {'trimStart': 4}, {'trimEnd': 5}])
def test_invalid_ranges(audio, config):
    with pytest.raises(ValueError):
        trim_audio([audio[0]], config)


@pytest.mark.parametrize('inputs', [[], [b'a', b'b']])
def test_requires_one_audio(inputs):
    with pytest.raises(ValueError, match='一个音频'):
        trim_audio(inputs, {})


def test_non_audio_rejected(monkeypatch):
    monkeypatch.setattr('app.audio_trim.probe', lambda path: {'streams': [{'codec_type': 'video'}]})
    with pytest.raises(ValueError, match='不含音轨'):
        trim_audio([b'video'], {})


def test_local_worker_cache_and_changed_range(tmp_path, monkeypatch, audio):
    store = Store(tmp_path / 'data')
    project = store.create_project('trim test')
    pid = project['id']
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    monkeypatch.setattr(worker.provider, 'submit', lambda *args: pytest.fail('must not call cloud'))
    asset = store.add_asset(pid, audio[0], 'source.wav')
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': node_id, 'type': 'studio', 'position': {'x': x, 'y': 0}, 'data': {'kind': kind, 'config': config}}
                       for node_id, x, kind, config in [('source', 0, 'asset.audio', {'assetId': asset['id']}),
                           ('trim', 300, 'audio.trim', {'trimStart': .25, 'trimEnd': 1.75})]]
    canvas['edges'] = [{'id': 'audio', 'source': 'source', 'target': 'trim', 'sourceHandle': 'audio', 'targetHandle': 'audio'}]
    store.save_canvas(pid, canvas, canvas['version'])
    def run(force=False):
        job = worker.submit(pid, ['trim'], force=force)
        while worker.tick():
            pass
        tasks = store.run(job['id'])['tasks']
        assert all(t['status'] == 'completed' for t in tasks), tasks
        result = next(t for t in tasks if t['node_id'] == 'trim')
        assert not result['submitted'] and not result['external_id']
        assert Store.queue_name(result['snapshot']) == 'local'
        return result
    first = run()
    assert run()['reused']
    assert not run(True)['reused']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data']['config']['trimEnd'] = 2.25
    store.save_canvas(pid, canvas, canvas['version'])
    changed = run()
    assert not changed['reused'] and changed['output'] != first['output']
    with wave.open(str(store.asset_path(changed['output']['assets'][0]))) as result:
        assert result.getnframes() / result.getframerate() == 2
    assert store.asset_path(asset['id']).read_bytes() == audio[0]
    assert DEFINITIONS['audio.trim']['inputs'] == DEFINITIONS['audio.trim']['outputs'] == {'audio': 'audio'}
    quote = quote_snapshot({'kind': 'audio.trim', 'config': {}}, {})
    assert quote['basis'] == 'local' and quote['amount'] == '0.000000'
