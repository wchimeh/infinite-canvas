from concurrent.futures import ThreadPoolExecutor
import io
import sqlite3
import time

from PIL import Image
import pytest

from app.costs import quote_snapshot
from app.credentials import Settings
from app.providers import TextProvider
from app.store import Store
from app.worker import Worker


def setup_project(tmp_path, kind='image.generate', mock=True):
    store = Store(tmp_path / 'projects')
    project = store.create_project('Review regression')
    project['settings']['cloudEnabled'] = True
    store.put_document(project['id'], 'project', project)
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [{'id': 'node', 'type': 'studio', 'position': {'x': 0, 'y': 0},
                        'data': {'kind': kind, 'config': {'prompt': 'test'}}}]
    store.save_canvas(project['id'], canvas, canvas['version'])
    return store, project, Worker(store, mock=mock, settings=Settings(tmp_path / 'settings'))


@pytest.mark.parametrize('kind', ['script.expand', 'shots.extract'])
def test_cloud_disabled_before_text_submission(tmp_path, monkeypatch, kind):
    store, project, worker = setup_project(tmp_path, kind, mock=False)
    calls = []
    monkeypatch.setattr(TextProvider, 'generate', lambda *args: calls.append(args) or {'text': 'ok'})
    run = worker.submit(project['id'])
    project['settings']['cloudEnabled'] = False
    store.put_document(project['id'], 'project', project)
    worker.tick()
    task = store.run(run['id'])['tasks'][0]
    assert not calls
    assert task['error_code'] == 'CLOUD_DISABLED'
    assert not task['submitted']
    assert not worker.ledger.summary(project['id'])['reservations']
    project['settings']['cloudEnabled'] = True
    store.put_document(project['id'], 'project', project)
    worker.retry(task['id'])
    worker.tick()
    assert store.task(task['id'])['status'] == 'completed'
    assert len(calls) == 1


def test_adopted_asset_wins_over_generated_cache(tmp_path):
    store, project, worker = setup_project(tmp_path)
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), 'red').save(buffer, 'PNG')
    asset = store.add_asset(project['id'], buffer.getvalue(), 'selected.png', 'node')
    canvas = store.canvas(project['id'])
    canvas['nodes'][0]['data']['config']['assetId'] = asset['id']
    store.save_canvas(project['id'], canvas, canvas['version'])
    for force in (False, True, False):
        run = worker.submit(project['id'], force=force)
        worker.tick()
        task = store.run(run['id'])['tasks'][0]
        assert task['status'] == 'completed'
        if force:
            assert task['output']['assets'] != [asset['id']]
        else:
            assert task['output']['assets'] == [asset['id']]
            assert task['input_hash'] is None


def test_legacy_database_migrates_concurrently(tmp_path):
    store, project, worker = setup_project(tmp_path)
    worker.submit(project['id'])
    before = store.tasks(project['id'])[0]
    path = store.project_dir(project['id']) / 'project.db'
    with sqlite3.connect(path) as con:
        columns = {row[1] for row in con.execute('PRAGMA table_info(tasks)')}
        if 'deadline_at' in columns:
            con.execute('ALTER TABLE tasks DROP COLUMN deadline_at')
        con.execute('PRAGMA user_version=1')
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda _: Store(store.root).task(before['id']), range(4)))
    assert all(row['deadline_at'] is None for row in rows)
    assert all(row['created_at'] == before['created_at'] and row['snapshot'] == before['snapshot'] for row in rows)


def test_timeout_retry_persists_new_window_without_resubmission(tmp_path):
    store, project, worker = setup_project(tmp_path)
    worker.submit(project['id'])
    task = store.tasks(project['id'])[0]
    tid = task['id']
    old_created = time.time() - 8000
    with store.db(tid) as con:
        con.execute('UPDATE tasks SET created_at=?,external_id=?,submitted=1 WHERE id=?', (old_created, 'remote', tid))
    quote = {'known': True, 'amount': '0.50', 'currency': 'CNY'}
    worker.ledger.reserve(project['id'], tid, quote)
    calls = []
    class Remote:
        def submit(self, *args):
            pytest.fail('must resume existing remote task')
        def poll(self, remote):
            calls.append(remote)
            return 'RUNNING'
    worker.provider = Remote()
    worker.tick()
    assert store.task(tid)['error_code'] == 'TASK_TIMEOUT'
    assert calls == ['remote']
    worker.retry(tid)
    worker.tick()
    assert calls == ['remote', 'remote']
    first = store.task(tid)
    assert first['deadline_at'] > time.time() + 7100
    restarted = Worker(Store(store.root), mock=True, settings=worker.settings)
    restarted.provider = Remote()
    store.update_task(tid, next_poll=0, lease_until=time.time() + 180)
    restarted.tick()
    after = store.task(tid)
    assert after['deadline_at'] == first['deadline_at']
    assert after['created_at'] == old_created
    assert after['snapshot'] == task['snapshot']
    assert len(worker.ledger.summary(project['id'])['reservations']) == 1
    store.update_task(tid, next_poll=0, deadline_at=time.time() - 1)
    restarted.tick()
    assert store.task(tid)['error_code'] == 'TASK_TIMEOUT'
    assert calls == ['remote', 'remote', 'remote', 'remote']


def test_new_submission_starts_window_after_queue_wait(tmp_path):
    store, project, worker = setup_project(tmp_path)
    worker.submit(project['id'])
    tid = store.tasks(project['id'])[0]['id']
    with store.db(tid) as con:
        con.execute('UPDATE tasks SET created_at=? WHERE id=?', (time.time() - 8000, tid))
    worker.tick()
    task = store.task(tid)
    assert task['status'] == 'completed'
    assert task['deadline_at'] > time.time() + 7100


@pytest.mark.parametrize('kind,config,extras,expected', [
    ('image.generate', {}, {}, 'image2'),
    ('image.variation', {'model': 'irrelevant'}, {}, 'image2'),
    ('video.image_to_video', {}, {}, 'ltx23'),
    ('video.image_to_video', {'model': 'wan22'}, {}, 'wan22'),
    ('video.sound_effects', {}, {}, 'mmaudio'),
    ('audio.tts', {}, {}, 'qwen'),
    ('audio.tts', {}, {'references': [{'mime': 'audio/wav'}]}, 'voxcpm2'),
    ('audio.tts', {}, {'links': [{'port': 'audio'}]}, 'voxcpm2'),
    ('script.expand', {'model': 'irrelevant'}, {}, 'configured-text'),
    ('shots.extract', {}, {}, 'configured-text'),
])
def test_quote_matches_workflow_model(kind, config, extras, expected):
    snapshot = {'kind': kind, 'config': config, 'textModel': 'configured-text', **extras}
    quote = quote_snapshot(snapshot, {expected: {'amount': '0.20', 'unit': 'task', 'currency': 'CNY'}})
    assert quote['model'] == expected
    assert quote['known'] and quote['amount'] == '0.200000'
