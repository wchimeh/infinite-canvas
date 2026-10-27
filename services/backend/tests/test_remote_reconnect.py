import time

import pytest
import httpx

from app.providers import ProviderError, RunningHub
from app.store import Store
from app.worker import Worker
from test_scheduler import prepare, settings
from test_core import png


@pytest.mark.parametrize('stage', ['poll', 'fetch'])
def test_remote_disconnect_survives_retry_limit_deadline_restart(tmp_path, stage):
    store = Store(tmp_path / 'data')
    project = prepare(store, count=1)
    worker = Worker(store, mock=True, settings=settings(tmp_path))
    worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    calls = []
    class Remote:
        offline = True
        def submit(self, *args):
            calls.append('submit')
            return 'remote-id'
        def poll(self, remote):
            assert remote == 'remote-id'
            if self.offline and stage == 'poll':
                raise ProviderError('PROVIDER_NETWORK', 'offline', True)
            return 'SUCCESS'
        def fetch(self, *args):
            if self.offline:
                raise ProviderError('PROVIDER_NETWORK', 'download interrupted', True)
            return [(png(), 'image.png')]
    remote = Remote()
    worker.provider = remote
    for i in range(8):
        store.update_task(tid, next_poll=0)
        if i:
            store.update_task(tid, deadline_at=time.time() - 1)
        worker.tick()
        task = store.task(tid)
        assert task['status'] == 'queued'
        assert task['error_code'] == 'REMOTE_RECONNECTING'
        assert task['external_id'] == 'remote-id'
        assert 0 < task['next_poll'] - time.time() <= 62
    store.update_task(tid, status='running', lease_until=0)
    store.recover()
    resumed = Worker(Store(store.root), mock=True, settings=worker.settings)
    resumed.provider = remote
    remote.offline = False
    store.update_task(tid, next_poll=0)
    resumed.tick()
    task = store.task(tid)
    assert task['status'] == 'completed' and task['error'] is None
    assert task['output']['assets'] and calls == ['submit']


@pytest.mark.parametrize('code', ['PROVIDER_NETWORK', 'PROVIDER_RATE_LIMIT', 'PROVIDER_UNAVAILABLE'])
def test_reconnect_running_clears_error_and_can_cancel(tmp_path, code):
    store = Store(tmp_path / 'data')
    project = prepare(store, count=1)
    worker = Worker(store, mock=True, settings=settings(tmp_path))
    worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    store.update_task(tid, external_id='remote', submitted=1, deadline_at=time.time() - 1)
    class Remote:
        offline = True
        def poll(self, remote):
            if self.offline:
                raise ProviderError(code, 'temporary', True)
            return 'RUNNING'
    remote = Remote(); worker.provider = remote
    worker.tick()
    assert store.task(tid)['error_code'] == 'REMOTE_RECONNECTING'
    remote.offline = False
    store.update_task(tid, next_poll=0)
    worker.tick()
    task = store.task(tid)
    assert task['status'] == 'queued' and task['error'] is None and task['attempt'] == 0
    assert task['deadline_at'] > time.time() + 7100
    store.cancel(tid)
    assert store.task(tid)['status'] == 'cancelled'


@pytest.mark.parametrize('failure', ['FAILED', 'PROVIDER_AUTH'])
def test_real_remote_failure_is_not_reconnected(tmp_path, failure):
    store = Store(tmp_path / 'data'); project = prepare(store, count=1)
    worker = Worker(store, mock=True, settings=settings(tmp_path)); worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    store.update_task(tid, external_id='remote', submitted=1)
    class Remote:
        def poll(self, remote):
            if failure == 'PROVIDER_AUTH':
                raise ProviderError(failure, 'auth')
            return failure
    worker.provider = Remote(); worker.tick()
    assert store.task(tid)['status'] == 'failed'
    assert store.task(tid)['error_code'] != 'REMOTE_RECONNECTING'


@pytest.mark.parametrize('status,retryable', [(403, False), (404, False), (408, True), (429, True), (503, True)])
def test_download_http_errors_are_classified(tmp_path, monkeypatch, status, retryable):
    monkeypatch.setattr('app.providers.build_workflow_request', lambda *args: {'result_node': ['1']})
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status))) as client:
        provider = RunningHub(client=client, settings=settings(tmp_path))
        monkeypatch.setattr(provider, 'request', lambda *args: [{'nodeId': '1', 'fileUrl': 'https://www.runninghub.cn/test.png', 'fileType': 'png'}])
        with pytest.raises(ProviderError) as error:
            provider.fetch('remote', 'image.generate', {}, {})
        assert error.value.retryable is retryable
        assert error.value.code == ('PROVIDER_UNAVAILABLE' if retryable else 'ASSET_DOWNLOAD_REJECTED')
