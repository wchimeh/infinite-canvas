import io
import pytest
from PIL import Image
from app.graph import DEFINITIONS
from test_text_input import setup


def test_nine_expansion_images_follow_port_order_and_enforce_limit(tmp_path, monkeypatch):
    store, project, worker = setup(tmp_path, monkeypatch)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][1]['data'].update(kind='prompt.video_expand', config={'prompt': 'Scene', 'seconds': 12})
    images, assets = [], []
    for index in range(1, 10):
        buffer = io.BytesIO()
        Image.new('RGB', (16, 16), (index * 20, 0, 0)).save(buffer, 'PNG')
        images.append(buffer.getvalue())
        assets.append(store.add_asset(pid, images[-1], f'{index}.png'))
        canvas['nodes'].append({'id': f'img{index}', 'position': {'x': 0, 'y': 0},
                                'data': {'kind': 'asset.image', 'config': {'assetId': assets[-1]['id']}}})
    for index in range(9, 0, -1):
        canvas['edges'].append({'id': f'img{index}', 'source': f'img{index}', 'target': 'script',
                                'sourceHandle': 'image', 'targetHandle': 'image' + (str(index) if index > 1 else ''), 'data': {'kind': 'data'}})
    store.save_canvas(pid, canvas, canvas['version'])
    run = worker.submit(pid, ['script'])
    for task in store.run(run['id'])['tasks']:
        if task['node_id'] != 'script':
            worker.tick(store.claim(worker.owner))
    target = next(t for t in store.run(run['id'])['tasks'] if t['node_id'] == 'script')
    assert worker.inputs(target)[1]['image'] == images
    assert len(DEFINITIONS['prompt.video_expand']['inputs']) == 16
    assert list(DEFINITIONS['prompt.video_expand']['inputs'].values()).count('image') == 9
    target['snapshot']['references'].append({'id': assets[0]['id'], 'mime': 'image/png', 'sha256': assets[0]['sha256']})
    with pytest.raises(ValueError, match='9'):
        worker.inputs(target)
