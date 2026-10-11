from concurrent.futures import ThreadPoolExecutor
import io
import threading
import time

from PIL import Image
import pytest

from app.costs import BudgetLedger
from app.credentials import Settings
from app.store import Store
from app.worker import Worker


def prepare(store, count=3, kind='image.generate', config=None):
    project = store.create_project('Scheduler QA')
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [{'id': str(i), 'type': 'studio', 'position': {'x': i * 300, 'y': 0},
                        'data': {'kind': kind, 'title': str(i), 'config': {'prompt': 'QA', **(config or {})}}} for i in range(count)]
    store.save_canvas(project['id'], canvas, canvas['version'])
    return project


def settings(tmp_path):
    return Settings(tmp_path / 'config')


def mixed_queue_tasks(store):
    project = store.create_project('Mixed queue QA')
    specs = [{'nodeId': str(i), 'deps': [], 'snapshot': {'kind': kind}}
             for i, kind in enumerate(['image.generate', 'video.image_to_video', 'image.generate', 'script.expand'])]
    run = store.create_run(project['id'], specs, False)
    return project, run


def test_media_capacity_shared_and_text_independent(tmp_path):
    store = Store(tmp_path)
    mixed_queue_tasks(store)
    limits = {'media': 2, 'text': 1}
    first = store.claim('qa', limits, queue='media')
    second = store.claim('qa', limits, queue='media')
    assert {first['snapshot']['kind'], second['snapshot']['kind']} == {'image.generate', 'video.image_to_video'}
    assert store.claim('qa', limits, queue='media') is None
    assert store.claim('qa', limits, queue='text')['snapshot']['kind'] == 'script.expand'
    store.update_task(first['id'], status='queued', external_id='remote-image', next_poll=time.time() + 60)
    assert store.claim('qa', limits, queue='media') is None
    store.update_task(first['id'], next_poll=0)
    assert store.claim('qa', limits, queue='media')['id'] == first['id']
    store.update_task(first['id'], status='completed')
    assert store.claim('qa', limits, queue='media')['snapshot']['kind'] == 'image.generate'


def test_independent_pools_run_text_while_media_is_blocked(tmp_path):
    store = Store(tmp_path / 'projects')
    mixed_queue_tasks(store)
    config = settings(tmp_path)
    config.save({'concurrency': {'media': 1, 'text': 1}})
    worker = Worker(store, mock=True, settings=config)
    media_entered, text_entered, release = threading.Event(), threading.Event(), threading.Event()
    names = {}
    def tick(task):
        queue = store.queue_name(task['snapshot'])
        names[queue] = threading.current_thread().name
        (text_entered if queue == 'text' else media_entered).set()
        release.wait(5)
        store.update_task(task['id'], status='completed')
    worker.tick = tick
    worker.start()
    try:
        assert media_entered.wait(3)
        assert text_entered.wait(3)
        assert names['text'].startswith('canvas-text')
        assert names['media'].startswith('canvas-media')
    finally:
        release.set()
        worker.close()


def test_media_concurrency_migrates_and_validates(tmp_path):
    import json
    config = settings(tmp_path)
    config.path.write_text(json.dumps({'concurrency': {'image': 2, 'video': 3}}))
    assert config.load()['concurrency']['media'] == 5
    config.save({'concurrency': {'media': 2, 'text': 3}})
    assert config.load()['concurrency']['media'] == 2
    assert config.load()['concurrency']['text'] == 3
    for invalid in (0, 9, True, 1.5):
        with pytest.raises(ValueError):
            config.save({'concurrency': {'media': invalid}})


def test_queue_summary_counts_projects_and_remote_slots(tmp_path):
    store = Store(tmp_path)
    for _ in range(2):
        project, run = mixed_queue_tasks(store)
        tasks = store.run(run['id'])['tasks']
        by_node = {t['node_id']: t for t in tasks}
        store.update_task(by_node['0']['id'], status='queued', external_id='remote')
        store.update_task(by_node['1']['id'], status='cancel_requested')
        store.update_task(by_node['2']['id'], status='completed')
    summary = {q['id']: q for q in store.queue_summary({'media': 2, 'text': 1, 'audio': 3})['queues']}
    assert summary['media'] == {'id': 'media', 'occupied': 4, 'waiting': 0, 'capacity': 2}
    assert summary['text'] == {'id': 'text', 'occupied': 0, 'waiting': 2, 'capacity': 1}
    assert summary['audio']['occupied'] == summary['audio']['waiting'] == 0


def test_queue_summary_api_is_authenticated_and_uses_current_limits(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    config = settings(tmp_path)
    with TestClient(create_app(root=tmp_path / 'projects', token='qa-token', start_worker=False, settings=config)) as client:
        assert client.get('/api/v1/queues').status_code == 401
        headers = {'Authorization': 'Bearer qa-token'}
        response = client.get('/api/v1/queues', headers=headers)
        assert response.status_code == 200
        config.save({'concurrency': {'media': 7}})
        data = client.get('/api/v1/queues', headers=headers).json()
        assert next(q for q in data['queues'] if q['id'] == 'media')['capacity'] == 7


def test_claim_capacity_is_atomic_across_projects(tmp_path):
    store = Store(tmp_path)
    for _ in range(2):
        project = prepare(store)
        Worker(store, mock=True).submit(project['id'])
    with ThreadPoolExecutor(max_workers=6) as pool:
        claims = list(pool.map(lambda i: store.claim(str(i), capacities={'image': 2}), range(6)))
    assert sum(task is not None for task in claims) == 2
    assert len({task['id'] for task in claims if task}) == 2


def test_character_images_serial_across_projects_and_polling(tmp_path):
    store = Store(tmp_path)
    for _ in range(2):
        project = prepare(store, 2, kind='image.character')
        Worker(store, mock=True).submit(project['id'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda i: store.claim(str(i), capacities={'media': 8}, queue='media'), range(4)))
    assert sum(t is not None for t in claims) == 1
    first = next(t for t in claims if t)
    store.update_task(first['id'], status='queued', external_id='remote-role', next_poll=time.time() + 60)
    assert store.claim('other', capacities={'media': 8}) is None
    store.update_task(first['id'], next_poll=0)
    assert store.claim('poll', capacities={'media': 8})['id'] == first['id']
    store.update_task(first['id'], status='completed')
    second = store.claim('next', capacities={'media': 8})
    assert second and second['id'] != first['id']
    project = prepare(store, 1, kind='image.generate')
    Worker(store, mock=True).submit(project['id'])
    ordinary = store.claim('ordinary', capacities={'media': 8})
    assert ordinary['snapshot']['kind'] == 'image.generate'


def test_character_images_serial_without_capacity_argument(tmp_path):
    store = Store(tmp_path)
    project = prepare(store, 2, kind='image.character')
    Worker(store, mock=True).submit(project['id'])
    assert store.claim('first')
    assert store.claim('second') is None


def test_remote_queued_occupies_slot_but_can_be_polled(tmp_path):
    store = Store(tmp_path)
    project = prepare(store, 2)
    Worker(store, mock=True).submit(project['id'])
    task = store.claim('first', capacities={'image': 1})
    store.update_task(task['id'], status='queued', external_id='remote-qa', next_poll=time.time() + 60)
    assert store.claim('other', capacities={'image': 1}) is None
    store.update_task(task['id'], next_poll=0)
    assert store.claim('poll', capacities={'image': 1})['id'] == task['id']


def test_worker_uses_pool_and_heartbeats_all_active_tasks(tmp_path):
    store = Store(tmp_path / 'projects')
    project = prepare(store, 2)
    config = settings(tmp_path)
    config.save({'concurrency': {'image': 2}})
    worker = Worker(store, mock=True, settings=config)
    worker.submit(project['id'], force=True)
    original = worker.provider.submit
    barrier = threading.Barrier(2)
    def submit(*args):
        barrier.wait(timeout=5)
        return original(*args)
    worker.provider.submit = submit
    worker.start()
    try:
        deadline = time.time() + 10
        while time.time() < deadline and any(t['status'] != 'completed' for t in store.tasks(project['id'])):
            time.sleep(0.05)
        assert all(t['status'] == 'completed' for t in store.tasks(project['id']))
    finally:
        worker.close()


def test_budget_rejection_occurs_before_submission(tmp_path):
    store = Store(tmp_path / 'projects')
    project = prepare(store, 1)
    project['settings'] = {'cloudEnabled': True, 'budget': {'limit': '0.10', 'currency': 'CNY'}}
    store.put_document(project['id'], 'project', project)
    config = settings(tmp_path)
    config.save({'pricing': {'image.generate': {'amount': '0.20', 'unit': 'task', 'currency': 'CNY'}}})
    worker = Worker(store, settings=config)
    class NoSubmit:
        version = 'qa'
        def submit(self, *args):
            raise AssertionError('must not call a paid provider')
    worker.provider = NoSubmit()
    run = worker.submit(project['id'])
    worker.tick()
    task = store.run(run['id'])['tasks'][0]
    assert task['status'] == 'failed'
    assert '预算' in task['error']
    assert not task['submitted']


def test_local_provider_is_allowed_without_cloud_and_template_is_frozen(tmp_path):
    store = Store(tmp_path / 'projects')
    project = prepare(store, 1, config={'provider': 'comfyui'})
    config = settings(tmp_path)
    template = {'version': 1, 'prompt': {'1': {'class_type': 'QA', 'inputs': {}}}, 'mappings': {}}
    config.save({'comfyWorkflows': {'image.generate': template}})
    worker = Worker(store, settings=config)
    run = worker.submit(project['id'])
    task = store.run(run['id'])['tasks'][0]
    assert task['snapshot']['providerId'] == 'comfyui'
    assert task['snapshot']['workflow'] == template
    config.save({'comfyWorkflows': {}})
    assert store.task(task['id'])['snapshot']['workflow'] == template


def test_new_paid_retry_keeps_previous_cost_and_checks_budget(tmp_path):
    store = Store(tmp_path)
    project = prepare(store, 1)
    project['settings']['budget'] = {'limit': '1', 'currency': 'CNY'}
    store.put_document(project['id'], 'project', project)
    worker = Worker(store, mock=True)
    worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    quote = {'known': True, 'amount': '0.60', 'currency': 'CNY'}
    worker.ledger.reserve(project['id'], tid, quote)
    store.update_task(tid, status='failed', submitted=1, external_id='charged', error_code='PROVIDER_TASK_FAILED')
    worker.retry(tid)
    assert worker.ledger.summary(project['id'])['estimatedUsed']['CNY'] == '0.600000'
    with pytest.raises(ValueError, match='预算'):
        worker.ledger.reserve(project['id'], tid, quote)


def test_remote_resume_keeps_original_reservation(tmp_path):
    store = Store(tmp_path)
    project = prepare(store, 1)
    worker = Worker(store, mock=True)
    worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    quote = {'known': True, 'amount': '0.60', 'currency': 'CNY'}
    worker.ledger.reserve(project['id'], tid, quote)
    store.update_task(tid, status='failed', submitted=1, external_id='remote', error_code='PROVIDER_NETWORK')
    worker.retry(tid)
    worker.ledger.reserve(project['id'], tid, quote)
    assert len(worker.ledger.summary(project['id'])['reservations']) == 1


def test_uncertain_text_submission_requires_confirmation(tmp_path, monkeypatch):
    from app.providers import ProviderError, TextProvider
    store = Store(tmp_path / 'projects')
    project = prepare(store, 1, kind='script.expand')
    project['settings']['cloudEnabled'] = True
    store.put_document(project['id'], 'project', project)
    worker = Worker(store, settings=settings(tmp_path))
    def uncertain(*args):
        raise ProviderError('TEXT_GENERATION_FAILED', 'response lost')
    monkeypatch.setattr(TextProvider, 'generate', uncertain)
    worker.submit(project['id'])
    worker.tick()
    task = store.tasks(project['id'])[0]
    assert task['error_code'] == 'SUBMIT_UNCERTAIN'
    with pytest.raises(ValueError, match='确认'):
        worker.retry(task['id'])
