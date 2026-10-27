from urllib.parse import unquote

from fastapi.testclient import TestClient

from app.credentials import Settings
from app.main import create_app
from app.store import Store
from test_core import png


def test_asset_download_attachment_preview_and_auth(tmp_path):
    store = Store(tmp_path / 'data')
    project = store.create_project('Download QA')
    asset = store.add_asset(project['id'], png(), '角色图.png')
    app = create_app(store.root, token='test', start_worker=False, settings=Settings(tmp_path / 'config'))
    with TestClient(app) as client:
        client.headers['host'] = 'localhost'
        url = '/api/v1/assets/' + asset['id'] + '/content'
        assert client.get(url + '?download=true').status_code in (401, 403)
        client.headers['authorization'] = 'Bearer test'
        preview = client.get(url)
        assert preview.status_code == 200 and preview.content == png()
        assert 'content-disposition' not in preview.headers
        downloaded = client.get(url + '?download=true')
        assert downloaded.content == preview.content
        assert downloaded.headers['content-disposition'].startswith('attachment;')
        assert '角色图.png' in unquote(downloaded.headers['content-disposition'])
        assert downloaded.headers['content-type'].startswith('image/png')
        assert client.get(url, headers={'Range': 'bytes=0-9'}).content == png()[:10]
