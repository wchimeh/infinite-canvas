import httpx
import pytest

from app.credentials import Settings
from app.providers import TextProvider, ProviderError
from app.store import Store
from app.worker import Worker


def setup(tmp_path, monkeypatch, story='一个年轻小伙赚大钱的故事', extra=''):
    settings = Settings(tmp_path / 'settings')
    settings.save({'textApiBase': 'https://text.invalid', 'textModel': 'qa-model'})
    monkeypatch.setattr(settings, 'key', lambda name: 'qa-key')
    store = Store(tmp_path / 'projects')
    p = store.create_project('Text input QA')
    p['settings']['cloudEnabled'] = True
    store.put_document(p['id'], 'project', p)
    c = store.canvas(p['id'])
    c['nodes'] = [{'id': id, 'type': 'studio', 'position': {'x': x, 'y': 0},
                   'data': {'kind': kind, 'config': {'prompt': prompt}}}
                  for id, x, kind, prompt in [('story', 0, 'story.prompt', story), ('script', 300, 'script.expand', extra)]]
    c['edges'] = [{'id': 'link', 'source': 'story', 'target': 'script', 'sourceHandle': 'text', 'targetHandle': 'text', 'data': {'kind': 'data'}}]
    store.save_canvas(p['id'], c, c['version'])
    return store, p, Worker(store, settings=settings)


@pytest.mark.parametrize('extra', ['', '限制在三百字以内'])
def test_upstream_reaches_http_user_message(tmp_path, monkeypatch, extra):
    store, p, worker = setup(tmp_path, monkeypatch, extra=extra)
    calls = []
    def post(client, url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': '第一场：年轻人开始创业。'}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    run = worker.submit(p['id'], ['script'])
    worker.tick(); worker.tick()
    assert len(calls) == 1
    assert calls[0]['messages'][1]['content'] == '一个年轻小伙赚大钱的故事' + ('\n\n' + extra if extra else '')
    assert all(t['status'] == 'completed' for t in store.run(run['id'])['tasks'])
    assert '一句话' in calls[0]['messages'][0]['content']
    script = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert script['snapshot']['adapterVersion'] == TextProvider.version


def test_empty_upstream_never_sends_http(tmp_path, monkeypatch):
    store, p, worker = setup(tmp_path, monkeypatch, story='  \n ')
    calls = []
    monkeypatch.setattr(httpx.Client, 'post', lambda *a, **kw: calls.append(kw))
    run = worker.submit(p['id'], ['script'])
    worker.tick(); worker.tick()
    script = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert calls == []
    assert script['status'] == 'failed'
    assert script['error_code'] == 'EMPTY_TEXT_INPUT'
