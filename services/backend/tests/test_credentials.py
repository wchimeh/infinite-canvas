import os
import uuid

import pytest

from app.credentials import Settings, WindowsVault


class MemoryVault:
    def __init__(self):
        self.values = {}

    def get(self, name):
        return self.values.get(name, '')

    def set(self, name, value):
        self.values[name] = value

    def delete(self, name):
        self.values.pop(name, None)


def test_credentials_are_masked_and_separate_from_configuration(tmp_path, monkeypatch):
    monkeypatch.delenv('RUNNINGHUB_API_KEY', raising=False)
    settings = Settings(tmp_path, vault=MemoryVault())
    settings.set_key('runninghub', 'qa-secret')
    assert settings.key('runninghub') == 'qa-secret'
    assert settings.public()['credentials']['runninghub']['configured']
    assert 'qa-secret' not in str(settings.public())
    settings.save({'textModel': 'test-model', 'concurrency': {'image': 2, 'video': 1, 'audio': 1, 'text': 1}})
    assert 'qa-secret' not in (tmp_path / 'settings.json').read_text()
    settings.delete_key('runninghub')
    assert not settings.public()['credentials']['runninghub']['configured']


def test_environment_override_can_be_identified_without_exposing_key(tmp_path, monkeypatch):
    settings = Settings(tmp_path, vault=MemoryVault())
    settings.set_key('text', 'vault-key')
    monkeypatch.setenv('TEXT_API_KEY', 'environment-key')
    assert settings.key('text') == 'environment-key'
    assert settings.public()['credentials']['text']['source'] == 'environment'
    settings.delete_key('text')
    assert settings.key('text') == 'environment-key'


@pytest.mark.parametrize('configuration', [
    {'apiKey': 'bad'}, {'concurrency': {'video': 99}}, {'concurrency': {'video': 0}},
    {'comfyUrl': 'http://192.168.1.1:8188'}, {'textApiBase': 'file:///secret'},
    {'pricing': {'model': {'amount': '-1', 'unit': 'task', 'currency': 'CNY'}}},
])
def test_configuration_rejects_invalid_or_secret_fields(tmp_path, configuration):
    settings = Settings(tmp_path, vault=MemoryVault())
    with pytest.raises(ValueError):
        settings.save(configuration)


def test_configuration_survives_reopen(tmp_path):
    settings = Settings(tmp_path, vault=MemoryVault())
    settings.save({'textApiBase': 'https://example.com/v1', 'textModel': 'model', 'comfyUrl': 'http://127.0.0.1:8188'})
    assert Settings(tmp_path, vault=MemoryVault()).public()['textModel'] == 'model'


@pytest.mark.skipif(os.name != 'nt', reason='Windows Credential Manager only')
def test_real_windows_vault_roundtrip():
    # 独立随机命名空间，避免改动任何用户已有凭据；finally 撤销测试记录。
    vault = WindowsVault(namespace='InfiniteCanvas-QA-' + uuid.uuid4().hex)
    try:
        vault.set('test', 'temporary-test-secret')
        assert vault.get('test') == 'temporary-test-secret'
    finally:
        vault.delete('test')
    assert vault.get('test') == ''
