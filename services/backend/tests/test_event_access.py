import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.credentials import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / 'data', token='test-event-session', start_worker=False,
                     settings=Settings(tmp_path / 'config'))
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize('host,origin,token', [
    ('remote.example', None, 'test-event-session'),
    ('remote.example', 'http://remote.example', 'test-event-session'),
    ('localhost:5173', 'http://remote.example', 'test-event-session'),
    ('localhost:5173', 'http://localhost:5173', 'incorrect'),
    ('localhost:5173', None, None),
])
def test_event_connection_rejects_invalid_access(client, host, origin, token):
    headers = {'host': host}
    if origin:
        headers['origin'] = origin
    if token:
        headers['authorization'] = 'Bearer ' + token
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect('/api/v1/events/ws?projectId=test', headers=headers):
            pytest.fail('Invalid event connection was accepted')
    assert error.value.code == 1008


@pytest.mark.parametrize('host', ['localhost:5173', '127.0.0.1:8765', 'testserver'])
def test_event_connection_accepts_local_session(client, host):
    store = client.app.state.store
    project = store.create_project('Event access test')
    with store.db(project['id']) as con:
        store.event(con, {'type': 'test.event', 'value': 'local'})
    headers = {'host': host, 'origin': 'http://' + host,
               'authorization': 'Bearer test-event-session'}
    with client.websocket_connect('/api/v1/events/ws?projectId=' + project['id'], headers=headers) as ws:
        event = ws.receive_json()
        assert event['type'] == 'test.event'
        assert event['value'] == 'local'
        assert event['eventId'] > 0


def test_http_and_events_reject_same_nonlocal_host(client):
    response = client.get('/api/v1/projects', headers={
        'host': 'remote.example', 'authorization': 'Bearer test-event-session'})
    assert response.status_code == 403
    assert response.json()['code'] == 'INVALID_HOST'
