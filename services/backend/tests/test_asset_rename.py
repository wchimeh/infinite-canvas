import pytest
from fastapi.testclient import TestClient

from app.credentials import Settings
from app.main import create_app
from app.store import Store
from test_core import png, node


def test_rename_preserves_file_identity_and_references(tmp_path):
    store = Store(tmp_path / 'data'); project = store.create_project('Rename QA')
    asset = store.add_asset(project['id'], png(), 'original.png')
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [node('ref', 'asset.image', assetId=asset['id'])]
    store.save_canvas(project['id'], canvas, canvas['version'])
    before = store.canvas(project['id'])
    app = create_app(tmp_path / 'data', token='test', start_worker=False, settings=Settings(tmp_path / 'config'))
    with TestClient(app) as client:
        client.headers.update({'host': 'localhost', 'authorization': 'Bearer test'})
        response = client.patch('/api/v1/assets/' + asset['id'], json={'name': '  主角三视图.png  '})
        assert response.status_code == 200, response.text
        updated = response.json()
        assert updated == {**asset, 'name': '主角三视图.png'}
        assert client.get('/api/v1/assets/' + asset['id'] + '/content').content == png()
    assert Store(store.root).asset(asset['id']) == updated
    assert store.canvas(project['id']) == before


@pytest.mark.parametrize('name', ['', '   ', 'x' * 201, 'folder/name', 'bad\\name', 'line\nbreak', None, 123])
def test_invalid_name_does_not_modify_asset(tmp_path, name):
    store = Store(tmp_path); project = store.create_project('QA')
    asset = store.add_asset(project['id'], png(), 'original.png')
    with pytest.raises(ValueError):
        store.rename_asset(asset['id'], name)
    assert store.asset(asset['id']) == asset


def test_rename_does_not_restore_deleted_asset(tmp_path):
    store = Store(tmp_path); project = store.create_project('QA')
    asset = store.add_asset(project['id'], png(), 'original.png')
    store.delete_asset(asset['id'])
    with pytest.raises(ValueError):
        store.rename_asset(asset['id'], 'new.png')
    assert store.assets(project['id']) == []
