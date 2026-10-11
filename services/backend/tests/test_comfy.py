import httpx
import pytest

from app.comfy import ComfyUI
from app.providers import ProviderError


def workflow():
    return {'image.generate': {'version': 1, 'prompt': {
        '1': {'class_type': 'Text', 'inputs': {'text': ''}},
        '2': {'class_type': 'Model', 'inputs': {'checkpoint': 'installed.safetensors'}},
    }, 'mappings': {'prompt': {'node': '1', 'input': 'text'}}}}


def transport(seen, missing=False):
    def handle(request):
        seen.append(request)
        if request.url.path == '/system_stats':
            return httpx.Response(200, json={'devices': [{'name': 'QA GPU', 'vram_total': 1024, 'vram_free': 512}]})
        if request.url.path == '/object_info':
            return httpx.Response(200, json={'Text': {'input': {'required': {'text': ['STRING', {}]}}},
                                            'Model': {'input': {'required': {'checkpoint': [['other.safetensors'] if missing else ['installed.safetensors'], {}]}}}})
        if request.url.path == '/prompt':
            return httpx.Response(200, json={'prompt_id': 'local-1', 'node_errors': {}})
        if request.url.path == '/history/local-1':
            return httpx.Response(200, json={'local-1': {'status': {'completed': True, 'status_str': 'success'},
                'outputs': {'9': {'images': [{'filename': 'output.png', 'subfolder': '', 'type': 'output'}]}}}})
        if request.url.path == '/view':
            return httpx.Response(200, content=b'fixture-output', headers={'content-type': 'image/png'})
        if request.url.path == '/upload/image':
            return httpx.Response(200, json={'name': 'uploaded.png', 'subfolder': '', 'type': 'input'})
        raise AssertionError(str(request.url))
    return httpx.MockTransport(handle)


def test_local_workflow_submit_poll_fetch_and_diagnostics():
    seen = []
    provider = ComfyUI('http://127.0.0.1:8188', workflow(), httpx.Client(transport=transport(seen)))
    assert provider.diagnostics()['ready']
    external = provider.submit('image.generate', {'prompt': 'a scene'}, {})
    assert external == 'local-1'
    assert provider.poll(external) == 'SUCCESS'
    assert provider.fetch(external, 'image.generate', {}, {}) == [(b'fixture-output', 'output.png')]
    import json
    submission = json.loads(next(r.content for r in seen if r.url.path == '/prompt'))
    assert submission['prompt']['1']['inputs']['text'] == 'a scene'
    assert workflow()['image.generate']['prompt']['1']['inputs']['text'] == ''


def test_missing_model_is_rejected_before_prompt():
    seen = []
    provider = ComfyUI('http://localhost:8188', workflow(), httpx.Client(transport=transport(seen, missing=True)))
    with pytest.raises(ProviderError, match='模型'):
        provider.submit('image.generate', {'prompt': 'test'}, {})
    assert not any(r.url.path == '/prompt' for r in seen)


def test_reference_is_uploaded_and_mapped():
    seen = []
    definitions = workflow()
    definitions['image.generate']['prompt']['1']['inputs']['image'] = ''
    definitions['image.generate']['mappings']['image'] = {'node': '1', 'input': 'image'}
    provider = ComfyUI('http://127.0.0.1:8188', definitions, httpx.Client(transport=transport(seen)))
    provider.submit('image.generate', {'prompt': 'test'}, {'image': [b'png']})
    assert any(r.url.path == '/upload/image' for r in seen)


@pytest.mark.parametrize('endpoint', ['http://192.168.0.1:8188', 'https://example.com', 'file:///secret', 'http://user:pass@localhost:8188'])
def test_remote_endpoint_rejected(endpoint):
    with pytest.raises(ValueError):
        ComfyUI(endpoint, {})


def test_unknown_status_is_not_accepted_as_success():
    provider = ComfyUI('http://localhost:8188', {}, httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={'local-1': {'status': {}}}))))
    assert provider.poll('local-1') == 'RUNNING'


def test_output_path_and_mime_validation():
    provider = ComfyUI('http://localhost:8188', {}, httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={'local-1': {'outputs': {'1': {'images': [{'filename': '../outside.png', 'type': 'output'}]}}}}))))
    with pytest.raises(ProviderError):
        provider.fetch('local-1', 'image.generate', {}, {})
