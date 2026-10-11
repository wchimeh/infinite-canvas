import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from zipfile import ZipFile

import pytest
from PIL import Image

from app.store import Store
from app.portable import export_project, import_project, export_template, import_template


def fixture(store):
    project = store.create_project('Portable project')
    pid = project['id']
    image = io.BytesIO()
    Image.new('RGB', (16, 16), 'navy').save(image, 'PNG')
    asset = store.add_asset(pid, image.getvalue(), 'reference.png')
    canvas = store.canvas(pid)
    canvas['nodes'] = [{'id': 'reference', 'type': 'studio', 'position': {'x': 40, 'y': 80},
                        'data': {'kind': 'asset.image', 'title': 'Reference', 'config': {'assetId': asset['id']},
                                 'status': 'completed', 'output': {'assets': [asset['id']]}}}]
    store.save_canvas(pid, canvas, canvas['version'])
    people = store.document(pid, 'people')
    people['characters'] = [{'id': 'hero', 'name': 'Hero', 'assetId': asset['id']}]
    store.put_document(pid, 'people', people, people['version'])
    store.put_document(pid, 'project', {**project, 'settings': {'cloudEnabled': True, 'apiKey': 'secret-fixture'}})
    return project, asset


def test_repeated_template_import_keeps_groups_separate(tmp_path):
    store = Store(tmp_path)
    project, _ = fixture(store)
    pid = project['id']
    canvas = store.canvas(pid)
    canvas['nodes'][0]['data']['groupId'] = 'original-group'
    store.save_canvas(pid, canvas, canvas['version'])
    template = export_template(store, pid)
    import_template(store, pid, template)
    result = import_template(store, pid, template)
    assert len({node['data']['groupId'] for node in result['nodes']}) == 3


def test_archive_excludes_cost_execution_history(tmp_path):
    from app.costs import BudgetLedger
    store = Store(tmp_path)
    project, _ = fixture(store)
    BudgetLedger(store).reserve(project['id'], 'private-cost-execution-marker',
                                {'known': True, 'amount': '1', 'currency': 'CNY'})
    with ZipFile(io.BytesIO(export_project(store, project['id']))) as archive:
        assert b'private-cost-execution-marker' not in archive.read('project.db')


def test_archive_roundtrip_remaps_and_excludes_secrets(tmp_path):
    source = Store(tmp_path / 'source')
    original, asset = fixture(source)
    archive = export_project(source, original['id'])
    with ZipFile(io.BytesIO(archive)) as package:
        manifest = json.loads(package.read('manifest.json'))
        assert manifest['format'] == 'infinite-canvas-project'
        for path, digest in manifest['files'].items():
            assert hashlib.sha256(package.read(path)).hexdigest() == digest
        assert b'secret-fixture' not in package.read('project.db')
    destination = Store(tmp_path / 'destination')
    imported = import_project(destination, archive)
    assert imported['id'] != original['id']
    new_asset = destination.assets(imported['id'])[0]
    assert new_asset['sha256'] == asset['sha256']
    assert destination.asset_path(new_asset['id']).read_bytes() == source.asset_path(asset['id']).read_bytes()
    assert destination.canvas(imported['id'])['nodes'][0]['data']['config']['assetId'] == new_asset['id']
    assert destination.document(imported['id'], 'people')['characters'][0]['assetId'] == new_asset['id']
    assert not imported['settings']['cloudEnabled']
    assert 'apiKey' not in imported['settings']
    assert destination.tasks(imported['id']) == []


def rewrite(archive, change):
    out = io.BytesIO()
    with ZipFile(io.BytesIO(archive)) as source, ZipFile(out, 'w') as target:
        for name in source.namelist():
            data = source.read(name)
            target.writestr(name, change(name, data))
    return out.getvalue()


def test_archive_rejects_tamper_and_does_not_leave_project(tmp_path):
    store = Store(tmp_path)
    project, _ = fixture(store)
    archive = export_project(store, project['id'])
    broken = rewrite(archive, lambda name, data: data + b'corrupt' if name.startswith('assets/') else data)
    before = [p['id'] for p in store.projects()]
    with pytest.raises(ValueError, match='hash|校验'):
        import_project(store, broken)
    assert [p['id'] for p in store.projects()] == before


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/outside', 'assets/../../escape', 'assets\\..\\escape'])
def test_archive_rejects_unsafe_entries(tmp_path, name):
    out = io.BytesIO()
    with ZipFile(out, 'w') as archive:
        archive.writestr(name, b'bad')
    with pytest.raises(ValueError):
        import_project(Store(tmp_path), out.getvalue())
    assert not (tmp_path.parent / 'escape').exists()


def test_template_reuse_removes_media_and_remaps_nodes(tmp_path):
    store = Store(tmp_path)
    project, _ = fixture(store)
    template = export_template(store, project['id'])
    assert template['format'] == 'infinite-canvas-template'
    assert 'assetId' not in template['canvas']['nodes'][0]['data']['config']
    assert 'output' not in template['canvas']['nodes'][0]['data']
    before = store.canvas(project['id'])
    result = import_template(store, project['id'], template)
    assert len(result['nodes']) == 2
    assert result['nodes'][0]['id'] != result['nodes'][1]['id']
    assert result['version'] > before['version']


def test_repeated_import_creates_independent_projects(tmp_path):
    store = Store(tmp_path)
    project, _ = fixture(store)
    archive = export_project(store, project['id'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        copies = list(pool.map(lambda _: import_project(store, archive), range(2)))
    assert len({copy['id'] for copy in copies}) == 2
    assert len(store.projects()) == 3
