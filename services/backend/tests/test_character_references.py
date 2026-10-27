import io

from PIL import Image

from app.generation_profiles import build_workflow_request
from app.graph import DEFINITIONS
from test_text_input import setup


def test_numbered_character_references_reach_workflow_in_order(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='image.character', config={'prompt': 'Character', 'workflowId': 'builtin-image2'})
    images = []
    for index, color in enumerate(['red', 'blue'], 1):
        buffer = io.BytesIO()
        Image.new('RGB', (16, 16), color).save(buffer, 'PNG')
        images.append(buffer.getvalue())
        asset = store.add_asset(pid, images[-1], f'{index}.png')
        canvas['nodes'].append({'id': f'image{index}', 'type': 'studio', 'position': {'x': 0, 'y': 0},
                                'data': {'kind': 'asset.image', 'config': {'assetId': asset['id']}}})
    for index in [2, 1]:
        canvas['edges'].append({'id': f'image{index}', 'source': f'image{index}', 'target': 'script',
                                'sourceHandle': 'image', 'targetHandle': 'image2' if index == 2 else 'image', 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] != 'script':
            worker.tick(store.claim(worker.owner))
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    config, inputs, _ = worker.inputs(target)
    assert inputs['image'] == images
    request = build_workflow_request('image.character', config, inputs, target['snapshot']['cloudWorkflow'])
    fields = [entry['fieldValue'] for entry in request['user_data'] if isinstance(entry['fieldValue'], bytes)]
    assert fields == images
    assert len(DEFINITIONS['image.character']['inputs']) == 9
