import io
import pytest
from PIL import Image
from app.graph import DEFINITIONS
from test_text_input import setup


@pytest.mark.parametrize('kind', ['image.generate', 'image.location', 'image.variation', 'image.character', 'image.prop'])
def test_image_ports_are_ordered(tmp_path, monkeypatch, kind):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']; canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind=kind, config={'prompt': 'image', 'workflowId': 'builtin-image2'})
    images = []
    for index, color in enumerate(['red', 'blue'], 1):
        buffer = io.BytesIO(); Image.new('RGB', (16, 16), color).save(buffer, 'PNG'); images.append(buffer.getvalue())
        asset = store.add_asset(pid, images[-1], f'{index}.png')
        canvas['nodes'].append({'id': f'image{index}', 'type': 'studio', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'asset.image', 'config': {'assetId': asset['id']}}})
    for index in [2, 1]:
        canvas['edges'].append({'id': f'image{index}', 'source': f'image{index}', 'target': 'script', 'sourceHandle': 'image', 'targetHandle': 'image2' if index == 2 else 'image', 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version']); run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] != 'script':
            worker.tick(store.claim(worker.owner))
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert worker.inputs(target)[1]['image'] == images
    assert len([port for port, type_ in DEFINITIONS[kind]['inputs'].items() if type_ == 'image']) == 8
