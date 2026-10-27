import base64
import subprocess
from types import SimpleNamespace

import pytest

from app import directory_picker as picker


def test_selected_path_passed_as_data(monkeypatch):
    initial = r"D:\中文 & $(exit) '项目"
    calls = []
    monkeypatch.setattr(picker, 'executable', lambda: 'powershell.exe')
    def run(args, **options):
        calls.append((args, options))
        return SimpleNamespace(stdout=initial)
    monkeypatch.setattr(picker.subprocess, 'run', run)
    assert picker.pick_directory(initial) == initial
    args, options = calls[0]
    assert initial not in base64.b64decode(args[-1]).decode('utf-16-le')
    assert options['env']['CANVAS_PICKER_INITIAL'] == initial
    assert options['timeout'] == 120 and options['check']


def test_cancel_and_parallel_requests(monkeypatch):
    monkeypatch.setattr(picker, 'executable', lambda: 'powershell.exe')
    def run(*args, **kwargs):
        with pytest.raises(ValueError, match='已经打开'):
            picker.pick_directory()
        return SimpleNamespace(stdout='')
    monkeypatch.setattr(picker.subprocess, 'run', run)
    assert picker.pick_directory() is None
    assert picker.pick_directory() is None


@pytest.mark.parametrize('failure,expected', [
    (subprocess.TimeoutExpired('powershell', 120), '超时'),
    (subprocess.CalledProcessError(1, 'powershell'), '无法打开'),
    (OSError('missing'), '无法打开'),
])
def test_failure_releases_lock(monkeypatch, failure, expected):
    monkeypatch.setattr(picker, 'executable', lambda: 'powershell.exe')
    def run(*args, **kwargs):
        raise failure
    monkeypatch.setattr(picker.subprocess, 'run', run)
    with pytest.raises(ValueError, match=expected):
        picker.pick_directory()
    assert not picker._lock.locked()


def test_unsupported_and_invalid_input(monkeypatch):
    monkeypatch.setattr(picker, 'executable', lambda: None)
    with pytest.raises(ValueError, match='不支持'):
        picker.pick_directory()
    with pytest.raises(ValueError, match='格式无效'):
        picker.pick_directory(None)


def test_api_auth_and_selection_does_not_save(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.credentials import Settings
    from app.main import create_app
    config = Settings(tmp_path / 'config')
    calls = []
    def select(initial):
        calls.append(initial)
        return str(tmp_path / 'selected')
    monkeypatch.setattr(picker, 'pick_directory', select)
    app = create_app(root=tmp_path / 'data', settings=config, token='qa', start_worker=False)
    with TestClient(app) as client:
        assert client.post('/api/v1/settings/storage/browse', json={}).status_code == 401
        assert calls == []
        client.headers['authorization'] = 'Bearer qa'
        response = client.post('/api/v1/settings/storage/browse', json={'directory': 'initial'})
        assert response.json()['directory'] == str(tmp_path / 'selected')
        assert calls == ['initial']
        assert not (config.root / 'project-storage.json').exists()
