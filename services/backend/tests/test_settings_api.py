import json

from fastapi.testclient import TestClient
import pytest

from app.credentials import Settings
from app.main import create_app


class MemoryVault:
    def __init__(self):
        self.values = {}
    def get(self, name):
        return self.values.get(name, '')
    def set(self, name, value):
        self.values[name] = value
    def delete(self, name):
        self.values.pop(name, None)


@pytest.fixture
def client(tmp_path, monkeypatch):
    for name in ('TEXT_API_KEY', 'RUNNINGHUB_API_KEY'):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(tmp_path / 'config', MemoryVault())
    with TestClient(create_app(tmp_path / 'projects', 'qa-token', start_worker=False, settings=settings)) as client:
        client.headers.update({'Authorization': 'Bearer qa-token'})
        yield client


def test_settings_credentials_never_return_secret(client):
    assert client.get('/api/v1/settings').status_code == 200
    response = client.put('/api/v1/settings/credentials/text', json={'key': 'private-test-key'})
    assert response.status_code == 200
    assert 'private-test-key' not in response.text
    assert client.get('/api/v1/settings').json()['credentials']['text']['configured']
    assert client.delete('/api/v1/settings/credentials/text').status_code == 200
    assert not client.get('/api/v1/settings').json()['credentials']['text']['configured']
    assert client.put('/api/v1/settings', json={'apiKey': 'invalid'}).status_code == 422


def test_archive_and_template_routes(client):
    project = client.post('/api/v1/projects', json={'name': 'API migration'}).json()
    pid = project['id']
    archive = client.get(f'/api/v1/projects/{pid}/archive')
    assert archive.status_code == 200
    assert archive.headers['content-type'].startswith('application/zip')
    imported = client.post('/api/v1/projects/import', files={'file': ('project.zip', archive.content, 'application/zip')})
    assert imported.status_code == 201
    assert imported.json()['id'] != pid
    template = client.get(f'/api/v1/projects/{pid}/template')
    assert template.status_code == 200
    assert client.post(f'/api/v1/projects/{pid}/template', json=template.json()).status_code == 200


def test_budget_configuration_and_estimate_are_validated(client):
    pid = client.post('/api/v1/projects', json={'name': 'Budget'}).json()['id']
    assert client.put(f'/api/v1/projects/{pid}/settings', json={'budget': {'limit': '-1', 'currency': 'CNY'}}).status_code == 422
    project = client.put(f'/api/v1/projects/{pid}/settings', json={'budget': {'limit': '10.50', 'currency': 'CNY'}}).json()
    assert project['settings']['budget']['limit'] == '10.500000'
    canvas = client.get(f'/api/v1/canvases/{pid}').json()
    canvas['nodes'] = [{'id': 'image', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'image.generate', 'config': {'prompt': 'QA'}}}]
    assert client.put(f'/api/v1/canvases/{pid}', json=canvas, headers={'If-Match': str(canvas['version'])}).status_code == 200
    estimate = client.post('/api/v1/runs/estimate', json={'projectId': pid}).json()
    assert estimate['unknownCount'] == 1
    assert client.get(f'/api/v1/projects/{pid}/tasks').json() == []
    assert client.get(f'/api/v1/projects/{pid}/costs').json()['actual'] is None


def test_configuration_routes_require_authentication(client):
    client.headers.pop('Authorization')
    assert client.get('/api/v1/settings').status_code == 401
    assert client.put('/api/v1/settings/credentials/text', json={'key': 'unauthorized'}).status_code == 401


def test_timeline_validation_and_composed_preview_route(client):
    pid = client.post('/api/v1/projects', json={'name': 'Preview'}).json()['id']
    timeline = client.get(f'/api/v1/projects/{pid}/timeline').json()
    assert client.post(f'/api/v1/projects/{pid}/preview').status_code == 400
    assert client.put(f'/api/v1/projects/{pid}/timeline', json={**timeline, 'audio': 'invalid'}).status_code == 400
    assert client.put(f'/api/v1/projects/{pid}/timeline', json={**timeline, 'fps': 30}).status_code == 200
