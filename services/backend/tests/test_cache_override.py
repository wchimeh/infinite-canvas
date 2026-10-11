from app.store import Store
from app.worker import Worker
from test_core import node, edge


def test_overwrite_updates_same_cache_without_forcing_dependencies(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('cache')['id']
    canvas = store.canvas(pid)
    canvas['nodes'] = [node('a', overwriteCache=True, prompt='story'), node('b', 'image.generate', prompt='scene')]
    canvas['edges'] = [edge('a', 'b')]
    store.save_canvas(pid, canvas, canvas['version'])
    worker = Worker(store, mock=True)

    def run():
        rid = worker.submit(pid, ['b'])['id']
        for _ in range(10):
            worker.tick()
        tasks = store.run(rid)['tasks']
        assert all(t['status'] == 'completed' for t in tasks)
        assert not next(t for t in tasks if t['node_id'] == 'a')['snapshot']['force']
        return next(t for t in tasks if t['node_id'] == 'b')

    original = run()
    assert run()['reused']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data']['config']['overwriteCache'] = True
    store.save_canvas(pid, canvas, canvas['version'])
    fresh = run()
    assert fresh['snapshot']['force'] and not fresh['reused']
    assert fresh['input_hash'] == original['input_hash']
    assert fresh['output']['assets'] != original['output']['assets']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data']['config']['overwriteCache'] = False
    store.save_canvas(pid, canvas, canvas['version'])
    reused = run()
    assert reused['reused'] and reused['output'] == fresh['output']
