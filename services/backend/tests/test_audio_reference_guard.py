import copy
import hashlib
from unittest.mock import Mock

import httpx
import pytest

from app.audio_reference_guard import validate_audio_labels, video_audio_indices
from app.credentials import Settings
from app.providers import ProviderError, TextProvider
from app.video_workflow import build_default_video_request
from app.worker import Worker
from test_shot_nodes import REWRITE


@pytest.mark.parametrize('text,count', [('<Audio 1> voice', 0), ('<Audio 2>', 1), ('<Audio 0>', 1)])
def test_unavailable_audio_labels_are_rejected(text, count):
    with pytest.raises(ValueError, match='音频'):
        validate_audio_labels(text, count)


def test_valid_audio_labels_and_plain_dialogue_remain_unchanged():
    validate_audio_labels('<Audio 1> and <Audio 2>', 2)
    validate_audio_labels('<d>[Chinese] 你好。</d>', 0)


def test_sparse_video_soundtrack_stays_paired_with_its_video():
    links = [{'source': 'v1', 'port': 'video', 'targetHandle': 'video'},
             {'source': 'v3', 'port': 'video', 'targetHandle': 'video3'},
             {'source': 'a3', 'port': 'video_audio', 'targetHandle': 'videoAudio3'}]
    deps = {key: {'output': {'assets': [key]}} for key in ['v1', 'v3', 'a3']}
    indices = video_audio_indices(links, deps)
    assert indices == [1]
    graph = build_default_video_request({'_videoAudioVideoIndices': indices}, {'video': [b'v1', b'v3'], 'video_audio': [b'a3']})['workflow']
    inputs = graph['136']['inputs']
    assert 'ref_video_audios.ref_video_audio_0' not in inputs
    assert 'ref_video_audios.ref_video_audio_1' in inputs
    assert video_audio_indices([links[0], links[2]], deps) == [2]


def test_orphan_soundtrack_forwarded_while_standalone_audio_is_supported():
    request = build_default_video_request({}, {'video_audio': [b'voice']})
    node, output = request['workflow']['136']['inputs']['ref_video_audios.ref_video_audio_0']
    assert request['workflow'][node]['class_type'] == 'LoadAudio' and output == 0
    assert any(item['nodeId'] == node and item['fieldValue'] == b'voice' for item in request['user_data'])
    assert 'ref_audios.ref_audio_0' not in request['workflow']['136']['inputs']
    graph = build_default_video_request({}, {'audio': [b'voice']})['workflow']
    assert 'ref_audios.ref_audio_0' in graph['136']['inputs']


def test_provider_ignores_audio_and_preserves_future_binding(tmp_path, monkeypatch):
    settings = Settings(tmp_path / 'settings')
    settings.save({'textApiBase': 'https://text.invalid', 'textModel': 'qa'})
    monkeypatch.setattr(settings, 'key', lambda _: 'qa-key')
    calls = []
    rewrite = REWRITE.replace('summary:', '<Audio 1> is a voice reference.\nsummary:')
    def post(client, url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': rewrite}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    convert = Mock(return_value=[])
    monkeypatch.setattr('app.providers.media_content', convert)
    provider = TextProvider(settings)
    future = provider.generate('prompt.video_expand', '场景，稍后将 Audio 1 接入视频节点', seconds=8)
    assert not future.get('referenceAudioHashes')
    assert 'Supplied audio references: 0' in calls[0]['messages'][1]['content']
    output = provider.generate('prompt.video_expand', '场景', seconds=8, audios=[b'voice'])
    assert 'referenceAudioHashes' not in output
    convert.assert_not_called()
    assert isinstance(calls[-1]['messages'][1]['content'], str)


def test_video_accepts_independent_audio_even_with_legacy_expansion_metadata(tmp_path):
    asset = tmp_path / 'audio.wav'; asset.write_bytes(b'actual')
    store = Mock(); store.asset_path.return_value = asset
    store.asset.return_value = {'mime': 'audio/wav', 'sha256': hashlib.sha256(b'actual').hexdigest()}
    worker = Worker(store, settings=Settings(tmp_path / 'settings'))
    task = {'deps': [], 'snapshot': {'kind': 'video.image_to_video', 'config': {'seconds': 8}, 'references': [],
        'links': [{'source': 'expand', 'port': 'text'}, {'source': 'audio', 'port': 'audio'}],
        'cloudWorkflow': {'builtin': 'minimax_h3'}, 'adapterVersion': 'qa', 'textModel': '', 'textEndpoint': ''}}
    deps = {'expand': {'snapshot': {'kind': 'prompt.video_expand'}, 'output': {'text': REWRITE + '\n<Audio 1>', 'referenceAudioHashes': ['different']}},
            'audio': {'output': {'assets': ['asset']}}}
    _, inputs, _ = worker.inputs(task, deps)
    assert inputs['audio'] == [b'actual']
    legacy = copy.deepcopy(deps); legacy['expand']['output'].pop('referenceAudioHashes')
    _, inputs, _ = worker.inputs(task, legacy)
    assert inputs['audio'] == [b'actual']
    store.update_task.assert_not_called()


def test_vision_model_ignores_legacy_audio_without_conversion(tmp_path, monkeypatch):
    settings = Settings(tmp_path / 'settings')
    settings.save({'textApiBase': 'https://text.invalid', 'textModel': 'qwen3.8-flash'})
    monkeypatch.setattr(settings, 'key', lambda _: 'qa-key')
    convert = Mock(); calls = []
    def post(client, url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': REWRITE}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr('app.providers.media_content', convert)
    monkeypatch.setattr(httpx.Client, 'post', post)
    TextProvider(settings).generate('prompt.video_expand', 'scene', audios=[b'voice'], seconds=8)
    convert.assert_not_called()
    assert isinstance(calls[0]['messages'][1]['content'], str)


def test_unpaired_audio_does_not_overwrite_paired_slot():
    links = [{'source': 'v', 'port': 'video', 'targetHandle': 'video3'},
             {'source': 'a', 'port': 'video_audio', 'targetHandle': 'videoAudio'},
             {'source': 'b', 'port': 'video_audio', 'targetHandle': 'videoAudio3'}]
    deps = {key: {'output': {'assets': [key]}} for key in ['v', 'a', 'b']}
    assert video_audio_indices(links, deps) == [1, 0]
