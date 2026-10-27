from app.store import Store


def test_old_active_tasks_remain_visible_without_duplicate_history(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('long project')['id']
    with store.db(pid) as con:
        for i in range(210):
            status = ['queued', 'running', 'cancel_requested'][i] if i < 3 else 'completed'
            con.execute('INSERT INTO tasks(id,run_id,node_id,status,snapshot,deps,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                        (f'{pid}_t{i}', 'run', f'node{i}', status, '{}', '[]', i, i))
        con.execute("UPDATE tasks SET status='running' WHERE created_at=209")
    tasks = store.tasks(pid)
    assert {f'{pid}_t{i}' for i in range(3)} <= {task['id'] for task in tasks}
    assert len(tasks) == len({task['id'] for task in tasks}) == 203
    assert [task['created_at'] for task in tasks] == sorted([task['created_at'] for task in tasks], reverse=True)
    assert not any(task['created_at'] == 3 for task in tasks)
