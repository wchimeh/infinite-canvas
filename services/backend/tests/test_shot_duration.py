import json

import httpx
import pytest

from app.providers import ProviderError, TextProvider
from test_text_input import setup


def generate_shots(tmp_path, monkeypatch, shot):
    _, _, worker = setup(tmp_path, monkeypatch)
    requests = []

    def post(client, url, **kwargs):
        requests.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps([shot])}}]},
                              request=httpx.Request('POST', url))

    monkeypatch.setattr(httpx.Client, 'post', post)
    result = TextProvider(settings=worker.settings).generate('shots.extract', '两个人跳舞')
    return result, requests


@pytest.mark.parametrize('duration', [4000, 5000, 15000])
def test_shot_duration_boundaries_accepted(tmp_path, monkeypatch, duration):
    shot = {'visualPrompt': '两个人跳舞', 'durationMs': duration}
    result, _ = generate_shots(tmp_path, monkeypatch, shot)
    assert result['shots'] == [shot]
    assert json.loads(result['text']) == [shot]


def test_shot_request_requires_actions_and_dialogue_to_fit_duration(tmp_path, monkeypatch):
    _, requests = generate_shots(tmp_path, monkeypatch, {'visualPrompt': '两个人跳舞', 'durationMs': 5000})
    instruction = requests[0]['messages'][0]['content']
    assert '4–15 秒' in instruction
    assert '4000–15000' in instruction
    assert '动作和对白必须能在该时长内完成' in instruction


@pytest.mark.parametrize('duration', [3999, 15001, 1000, 30000, 4000.5, '5000', None, True])
def test_invalid_shot_duration_rejected(tmp_path, monkeypatch, duration):
    with pytest.raises(ProviderError) as error:
        generate_shots(tmp_path, monkeypatch, {'visualPrompt': '跳舞', 'durationMs': duration})
    assert error.value.code == 'TEXT_GENERATION_FAILED'


def test_missing_shot_duration_rejected(tmp_path, monkeypatch):
    with pytest.raises(ProviderError) as error:
        generate_shots(tmp_path, monkeypatch, {'visualPrompt': '跳舞'})
    assert error.value.code == 'TEXT_GENERATION_FAILED'


@pytest.mark.parametrize('field', ['title', 'dialogue', 'shotSize', 'cameraMove'])
@pytest.mark.parametrize('value', [{'bad': 'object'}, ['array'], None, 12, True])
def test_non_text_shot_fields_rejected(tmp_path, monkeypatch, field, value):
    with pytest.raises(ProviderError) as error:
        generate_shots(tmp_path, monkeypatch, {'visualPrompt': '跳舞', 'durationMs': 5000, field: value})
    assert error.value.code == 'TEXT_GENERATION_FAILED'


def test_optional_shot_text_fields_preserved(tmp_path, monkeypatch):
    shot = {'visualPrompt': '跳舞', 'durationMs': 5000, 'title': '起舞', 'dialogue': '', 'shotSize': '全景', 'cameraMove': '固定'}
    result, _ = generate_shots(tmp_path, monkeypatch, shot)
    assert result['shots'] == [shot]
