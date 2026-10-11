import io

import pytest
from PIL import Image

from app.store import Store


@pytest.mark.parametrize('kind,group,key,name', [
    ('image.character', 'characters', 'characterId', '林夏'),
    ('image.location', 'locations', 'locationId', '咖啡馆'),
    ('image.location', 'locations', 'locationId', '街道/雨夜:入口'),
])
def test_generated_image_subject_prefix(tmp_path, kind, group, key, name):
    store = Store(tmp_path); pid = store.create_project('Names')['id']
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': 'node', 'data': {'kind': kind, 'title': 'fallback', 'config': {key: 'subject'}}}]
    store.save_canvas(pid, canvas, canvas['version'])
    people = store.document(pid, 'people'); people[group] = [{'id': 'subject', 'name': name}]
    store.put_document(pid, 'people', people)
    data = io.BytesIO(); Image.new('RGB', (2, 2)).save(data, format='PNG')
    original = store.add_asset(pid, data.getvalue(), 'image_1.png')
    asset = store.add_asset(pid, data.getvalue(), 'image_1.png', 'node', 'run')
    assert asset['name'] == name.replace('/', '_').replace(':', '_') + '_image_1.png'
    assert original['name'] == 'image_1.png'
    assert asset['sha256'] == original['sha256'] and asset['path'] == original['path']
    assert store.asset_path(asset['id']).read_bytes() == data.getvalue()
    assert store.asset(asset['id'])['name'] == asset['name']
    assert store.add_asset(pid, b'audio', 'voice.wav', 'node')['name'] == 'voice.wav'


@pytest.mark.parametrize('title,expected', [('镜头一', '镜头一_original.png'), ('', 'original.png')])
def test_missing_subject_uses_title_and_missing_node_keeps_name(tmp_path, title, expected):
    store = Store(tmp_path); pid = store.create_project('Fallback')['id']
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': 'node', 'data': {'kind': 'image.character', 'title': title, 'config': {'characterId': 'deleted'}}}]
    store.save_canvas(pid, canvas, canvas['version'])
    data = io.BytesIO(); Image.new('RGB', (2, 2)).save(data, format='PNG')
    assert store.add_asset(pid, data.getvalue(), 'original.png', 'node')['name'] == expected
    assert store.add_asset(pid, data.getvalue(), 'original.png', 'missing')['name'] == 'original.png'
