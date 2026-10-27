import json

import httpx
import pytest

from app.text_transport import TextTransportError, receive_text


def call(body, stream=True, status=200):
    transport = httpx.MockTransport(lambda request: httpx.Response(status, content=body))
    with httpx.Client(transport=transport) as client:
        return receive_text(client, 'https://example.test/chat/completions', {}, {}, stream)


def event(delta, finish=None):
    return 'data: ' + json.dumps({'choices': [{'delta': delta, 'finish_reason': finish}]}) + '\n\n'


def test_stream_ignores_thinking_and_usage():
    body = ': heartbeat\n\n' + event({'reasoning_content': 'private reasoning'})
    body += event({'content': 'hello '}) + event({'content': 'world'}, 'stop')
    body += 'data: {"choices":[],"usage":{}}\n\ndata: [DONE]\n\n'
    assert call(body) == 'hello world'


@pytest.mark.parametrize('body', [event({'content': 'partial'}), event({'content': 'partial'}, 'length'), 'data: broken\n\n', 'data: [DONE]\n\n'])
def test_incomplete_stream_never_returns_partial_result(body):
    with pytest.raises(TextTransportError):
        call(body)


def test_non_stream_remains_compatible():
    assert call(json.dumps({'choices': [{'message': {'content': 'done'}}]}), stream=False) == 'done'


@pytest.mark.parametrize('failure,code', [(httpx.ConnectTimeout, 'TEXT_CONNECT_TIMEOUT'), (httpx.ReadTimeout, 'TEXT_READ_TIMEOUT'), (httpx.RemoteProtocolError, 'TEXT_STREAM_INTERRUPTED')])
def test_network_errors_are_distinct(failure, code):
    def handler(request):
        raise failure('sensitive upstream detail')
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(TextTransportError) as caught:
            receive_text(client, 'https://example.test/chat/completions', {}, {}, True)
    assert caught.value.code == code
    assert 'sensitive' not in str(caught.value)


@pytest.mark.parametrize('mode,expected', [('default', None), ('on', True), ('off', False)])
def test_provider_sends_thinking_and_stream_parameters(monkeypatch, mode, expected):
    from app.providers import TextProvider
    class Settings:
        def load(self):
            return {'textApiBase': 'https://example.test/v1', 'textModel': 'qwen3.8-flash'}
        def key(self, name):
            return 'fake'
    seen = []
    def handle(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, text=event({'content': '正文'}, 'stop') + 'data: [DONE]\n\n')
    real_client = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs))
    assert TextProvider(Settings()).generate('script.expand', '故事', thinking_mode=mode, stream=True) == {'text': '正文'}
    assert seen[0]['stream'] is True
    if expected is None:
        assert 'enable_thinking' not in seen[0]
    else:
        assert seen[0]['enable_thinking'] is expected
