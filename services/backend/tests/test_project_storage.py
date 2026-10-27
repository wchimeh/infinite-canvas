from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.credentials import Settings
from app.main import create_app
from app.project_storage import ProjectStorage
from app.store import Store
from test_core import png


def test_save_restart_and_preserve_original(tmp_path):
    config = Settings(tmp_path / 'config')
    original = Store(tmp_path / 'original')
    project = original.create_project('existing')
    asset = original.add_asset(project['id'], png(), 'image.png')
    target = tmp_path / 'new projects'
    app = create_app(default_root=original.root, settings=config, token='qa', start_worker=False)
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost'})
        assert client.put('/api/v1/settings/storage', json={'directory': str(target)}).status_code == 401
        client.headers['authorization'] = 'Bearer qa'
        response = client.put('/api/v1/settings/storage', json={'directory': str(target)})
        assert response.status_code == 200, response.text
        assert response.json()['restartRequired']
        assert app.state.store.root == original.root
        assert len(client.get('/api/v1/projects').json()) == 1
    restarted = create_app(default_root=original.root, settings=config, token='qa', start_worker=False)
    assert restarted.state.store.root == target
    assert restarted.state.store.projects() == []
    assert original.asset_path(asset['id']).read_bytes() == png()
    assert config.root == tmp_path / 'config'


def test_cancel_and_explicit_root_isolation(tmp_path):
    config = Settings(tmp_path / 'config')
    original = tmp_path / 'original'
    storage = ProjectStorage(config.root)
    storage.save(str(tmp_path / 'saved'))
    app = create_app(root=original, settings=config, token='qa', start_worker=False)
    assert app.state.store.root == original
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost', 'authorization': 'Bearer qa'})
        response = client.delete('/api/v1/settings/storage')
        assert response.status_code == 200 and not response.json()['restartRequired']
    assert storage.resolve(original) == original


@pytest.mark.parametrize('value', ['', 'relative/data', None, 123, '../data'])
def test_invalid_path_preserves_settings(tmp_path, value):
    storage = ProjectStorage(tmp_path / 'config')
    target = storage.save(str(tmp_path / 'valid'))
    with pytest.raises(ValueError):
        storage.save(value)
    assert storage.resolve(tmp_path / 'fallback') == target


def test_file_and_drive_root_rejected(tmp_path):
    storage = ProjectStorage(tmp_path / 'config')
    file = tmp_path / 'file'; file.write_text('keep')
    for target in [str(file), str(Path(tmp_path.anchor))]:
        with pytest.raises(ValueError):
            storage.save(target)
    assert file.read_text() == 'keep'


def test_unavailable_saved_directory_falls_back(tmp_path):
    config = Settings(tmp_path / 'config')
    storage = ProjectStorage(config.root)
    target = tmp_path / 'next'
    storage.save(str(target))
    target.rmdir(); target.write_text('file replaced directory')
    app = create_app(default_root=tmp_path / 'fallback', settings=config, token='qa', start_worker=False)
    assert app.state.store.root == tmp_path / 'fallback'
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost', 'authorization': 'Bearer qa'})
        status = client.get('/api/v1/settings/storage').json()
        assert status['startupError'] and status['nextDirectory'] == str(target)


def test_config_write_failure_preserves_previous_directory(tmp_path, monkeypatch):
    storage = ProjectStorage(tmp_path / 'config')
    previous = storage.save(str(tmp_path / 'previous'))

    def fail_replace(*args):
        raise PermissionError('config locked')

    monkeypatch.setattr('app.project_storage.os.replace', fail_replace)
    with pytest.raises(ValueError, match='配置.*写入失败'):
        storage.save(str(tmp_path / 'next'))
    assert storage.resolve(tmp_path / 'fallback') == previous
    assert not list(storage.path.parent.glob('*.partial'))


@pytest.mark.parametrize('operation', ['save', 'cancel'])
def test_successful_update_clears_startup_error(tmp_path, operation):
    config = Settings(tmp_path / 'config')
    storage = ProjectStorage(config.root)
    storage.path.write_text('broken json', encoding='utf-8')
    app = create_app(default_root=tmp_path / 'fallback', settings=config, token='qa', start_worker=False)
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost', 'authorization': 'Bearer qa'})
        assert client.get('/api/v1/settings/storage').json()['startupError']
        assert client.put('/api/v1/settings/storage', json={'directory': 'relative'}).status_code == 400
        assert client.get('/api/v1/settings/storage').json()['startupError']
        response = (client.put('/api/v1/settings/storage', json={'directory': str(tmp_path / 'next')})
                    if operation == 'save' else client.delete('/api/v1/settings/storage'))
        assert response.status_code == 200
        assert client.get('/api/v1/settings/storage').json()['startupError'] == ''
