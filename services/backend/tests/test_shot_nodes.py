import json
import io

import httpx
import pytest
from PIL import Image

from app.costs import quote_snapshot
from app.generation_profiles import resolve_selection
from app.graph import DEFINITIONS
from app.providers import ProviderError, TextProvider
from app.store import Store
from test_text_input import setup


SHOT = {'title': '相遇', 'visualPrompt': '图片1的女人与图片2的男人相遇',
        'dialogue': '你好。', 'cameraMove': '固定镜头', 'shotSize': '中景', 'durationMs': 8000}
REWRITE = ('subject_definitions:\n<Subject 1> is the woman in <Picture 1>.\n'
           'summary:\n[reference generation] An 8-second greeting.\n'
           'retention_analysis:\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep her identity.\n'
           'detailed_description:\nA realistic scene. [Shot 1] <Subject 1> (S1) says <d>[Chinese] 你好。</d>\n'
           'overall_soundscape:\nQuiet room tone.\nnon_diegetic_music:\nN/A')


def select_config(shot=SHOT):
    return {'shotIndex': 0, 'selectedShot': shot}


def test_new_node_contracts():
    assert DEFINITIONS['shots.select']['inputs'] == {'text': 'text'}
    assert DEFINITIONS['shots.select']['outputs'] == {'text': 'text'}
    assert DEFINITIONS['prompt.video_expand']['inputs']['text'] == 'text'


def test_selection_outputs_only_selected_shot():
    from app.shot_nodes import select_shot
    other = {**SHOT, 'title': '告别', 'durationMs': 12000}
    output = select_shot([SHOT, other], {'shotIndex': 1, 'selectedShot': other})
    assert output['shot'] == other
    assert output['seconds'] == 12
    assert output['text'].splitlines()[0] == '分镜：告别'
    assert '你好。' in output['text'] and '固定镜头' in output['text']


@pytest.mark.parametrize('config', [{}, {'shotIndex': 4, 'selectedShot': SHOT},
                                    {'shotIndex': True, 'selectedShot': SHOT},
                                    {'shotIndex': 0, 'selectedShot': {**SHOT, 'title': '旧条目'}}])
def test_invalid_selection_requires_reselection(config):
    from app.shot_nodes import select_shot
    with pytest.raises(ValueError, match='选择'):
        select_shot([SHOT], config)


@pytest.mark.parametrize('seconds', [3, 16])
def test_selection_rejects_old_out_of_range_shots(seconds):
    from app.shot_nodes import select_shot
    shot = {**SHOT, 'durationMs': seconds * 1000}
    with pytest.raises(ValueError, match='4–15'):
        select_shot([shot], select_config(shot))


def test_selection_local_and_expansion_text_routing():
    assert Store.queue_name({'kind': 'shots.select'}) == 'local'
    assert Store.queue_name({'kind': 'prompt.video_expand'}) == 'text'
    assert quote_snapshot({'kind': 'shots.select', 'config': {}}, {})['amount'] == '0.000000'
    selection = resolve_selection({}, 'prompt.video_expand', {})
    assert selection['textServiceId'] == 'legacy'
    quote = quote_snapshot({'kind': 'prompt.video_expand', 'config': {}, 'textModel': 'qa-model'},
                           {'text/qa-model': {'amount': '0.1', 'unit': 'task', 'currency': 'CNY'}})
    assert quote['provider'] == 'text' and quote['known']


def test_select_runs_locally_and_propagates_duration(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='shots.select', config=select_config())
    canvas['nodes'].append({'id': 'expand', 'type': 'studio', 'position': {'x': 600, 'y': 0},
                            'data': {'kind': 'prompt.video_expand', 'config': {'seconds': 5}}})
    canvas['edges'].append({'id': 'expand', 'source': 'script', 'target': 'expand',
                           'sourceHandle': 'text', 'targetHandle': 'text', 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    # Selection alone must work with cloud disabled.
    project['settings']['cloudEnabled'] = False; store.put_document(pid, 'project', project)
    run = worker.submit(pid, ['script'])
    source = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'story')
    store.update_task(source['id'], status='completed', output={'text': json.dumps([SHOT]), 'shots': [SHOT]})
    assert worker.tick()
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert target['status'] == 'completed' and target['submitted'] == 0
    assert target['output']['shot'] == SHOT and target['output']['seconds'] == 8
    project['settings']['cloudEnabled'] = True; store.put_document(pid, 'project', project)
    run = worker.submit(pid, ['expand'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] == 'story':
            store.update_task(task['id'], status='completed', output={'text': json.dumps([SHOT]), 'shots': [SHOT]})
        elif task['node_id'] == 'script':
            store.update_task(task['id'], status='completed', output=target['output'])
    expansion = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'expand')
    config, _, _ = worker.inputs(expansion)
    assert config['seconds'] == 8


@pytest.mark.parametrize('content', [REWRITE, 'A plain translation.', REWRITE.replace('retention_analysis:', 'analysis:')])
def test_expansion_uses_reference_guide_and_checks_sections(tmp_path, monkeypatch, content):
    _, _, worker = setup(tmp_path, monkeypatch)
    requests = []
    def post(client, url, **kwargs):
        requests.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': content}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    provider = TextProvider(settings=worker.settings)
    if content != REWRITE:
        with pytest.raises(ProviderError):
            provider.generate('prompt.video_expand', '两个人相遇')
    else:
        assert provider.generate('prompt.video_expand', '两个人相遇')['text'] == REWRITE
    system = requests[0]['messages'][0]['content']
    assert 'Full-Reference Mode Rewrite Output Format Guide' in system
    assert 'subject_definitions' in system and '<Picture N>' in system
    assert '4–15' in system
    assert 'specific gaze target' in system
    assert 'A locked camera does not freeze the actors' in system
    assert 'Character turnaround sheets supply identity' in system
    assert 'Preserve intentional gaze avoidance' in system
    assert 'remove optional gestures and extra cuts first' in system
    assert 'silently check gaze targets' in system


def test_expansion_images_order_and_duration_reach_request(tmp_path, monkeypatch):
    _, _, worker = setup(tmp_path, monkeypatch)
    requests = []
    def post(client, url, **kwargs):
        requests.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content': REWRITE}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    images = []
    for color in ('red', 'blue'):
        data = io.BytesIO(); Image.new('RGB', (8, 8), color).save(data, format='PNG'); images.append(data.getvalue())
    result = TextProvider(settings=worker.settings).generate('prompt.video_expand', '两个人相遇', seconds=8, images=images)
    assert result['seconds'] == 8
    content = requests[0]['messages'][1]['content']
    assert '8 seconds' in content[0]['text']
    assert '<Picture 1>' in content[1]['text'] and '<Picture 2>' in content[3]['text']
    assert content[2]['image_url']['url'].startswith('data:image/jpeg;base64,')
    assert content[2]['image_url']['url'] != content[4]['image_url']['url']


def test_expansion_executes_in_text_queue_then_video_inherits_duration(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 5})
    canvas['nodes'].append({'id': 'video', 'type': 'studio', 'position': {'x': 600, 'y': 0},
                            'data': {'kind': 'video.image_to_video', 'config': {'seconds': 5}}})
    canvas['edges'].append({'id': 'video', 'source': 'script', 'target': 'video',
                           'sourceHandle': 'text', 'targetHandle': 'text', 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['video'])
    source = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'story')
    store.update_task(source['id'], status='completed', output={'text': '两个人相遇', 'seconds': 8})
    def post(client, url, **kwargs):
        assert '8 seconds' in kwargs['json']['messages'][1]['content']
        return httpx.Response(200, json={'choices': [{'message': {'content': REWRITE}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    expansion = store.claim('qa', queue='text')
    assert expansion['node_id'] == 'script'
    worker.tick(expansion)
    result = store.task(expansion['id'])
    assert result['status'] == 'completed' and result['submitted'] == 1
    assert result['output'] == {'text': REWRITE, 'seconds': 8}
    video = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'video')
    config, _, _ = worker.inputs(video)
    assert config['seconds'] == 8 and config['prompt'] == REWRITE


def test_performance_rules_invalidate_only_expansion_cache(tmp_path, monkeypatch):
    from app.shot_nodes import EXPANSION_VERSION
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 8})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    tasks = store.run(run['id'])['tasks']
    source = next(t for t in tasks if t['node_id'] == 'story')
    assert source['snapshot']['adapterVersion'] == worker.provider.version
    store.update_task(source['id'], status='completed', output={'text': 'A greets B.'})
    target = next(t for t in tasks if t['node_id'] == 'script')
    assert target['snapshot']['adapterVersion'] == f'{TextProvider.version}/{EXPANSION_VERSION}'
    _, _, new_hash = worker.inputs(target)
    target['snapshot']['adapterVersion'] = TextProvider.version
    _, _, old_hash = worker.inputs(target)
    assert new_hash != old_hash


def test_invalid_reference_image_rejected_before_http(tmp_path, monkeypatch):
    _, _, worker = setup(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(httpx.Client, 'post', lambda *args, **kwargs: calls.append(kwargs))
    with pytest.raises(ProviderError) as error:
        TextProvider(settings=worker.settings).generate('prompt.video_expand', '跳舞', images=[b'corrupt'])
    assert error.value.code == 'INVALID_INPUT'
    assert calls == []


def test_inherited_text_duration_rechecked_against_budget(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; project['settings']['budget'] = {'limit': '0.6', 'currency': 'CNY'}
    store.put_document(pid, 'project', project)
    worker.settings.save({'pricing': {'text/qa-model': {'amount': '0.1', 'unit': 'second', 'currency': 'CNY'}}})
    canvas = store.canvas(pid); canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 5})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    source = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'story')
    store.update_task(source['id'], status='completed', output={'text': '跳舞', 'seconds': 8})
    calls = []
    def post(client, url, **kwargs):
        calls.append(kwargs)
        return httpx.Response(200, json={'choices': [{'message': {'content': REWRITE}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.Client, 'post', post)
    worker.tick()
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert target['status'] == 'failed' and target['submitted'] == 0
    assert calls == []


def test_invalid_expansion_duration_not_marked_submitted(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'seconds': 30})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    worker.tick(); worker.tick()
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert target['status'] == 'failed' and target['submitted'] == 0
    assert target['error_code'] == 'INVALID_INPUT'


def test_truncated_jpeg_worker_never_submits_or_reserves(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; data = io.BytesIO()
    Image.new('RGB', (16, 16), 'red').save(data, format='JPEG')
    asset = store.add_asset(pid, data.getvalue()[:-2], 'truncated.jpg')
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'referenceIds': [asset['id']]})
    store.save_canvas(pid, canvas, canvas['version'])
    calls = []
    monkeypatch.setattr(httpx.Client, 'post', lambda *args, **kwargs: calls.append(kwargs))
    run = worker.submit(pid, ['script']); worker.tick(); worker.tick()
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert target['status'] == 'failed' and target['error_code'] == 'INVALID_INPUT'
    assert target['submitted'] == 0 and calls == []
    with store.db(pid) as con:
        exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='cost_reservations'").fetchone()
        if exists:
            assert con.execute('SELECT COUNT(*) FROM cost_reservations WHERE task_id=?', (target['id'],)).fetchone()[0] == 0
