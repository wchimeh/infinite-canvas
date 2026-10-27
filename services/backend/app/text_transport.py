"""OpenAI-compatible response transport; never publish reasoning or raw errors."""
import json
import time

import httpx


class TextTransportError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def check_status(response):
    codes = {401: ('PROVIDER_AUTH', '文本服务身份验证失败，请检查密钥和模型权限'),
             403: ('PROVIDER_AUTH', '文本服务身份验证失败，请检查密钥和模型权限'),
             404: ('MODEL_UNAVAILABLE', '文本服务地址或模型不存在，请修正配置'),
             429: ('PROVIDER_RATE_LIMIT', '文本服务限流，请稍后手动重试')}
    if response.status_code in codes:
        raise TextTransportError(*codes[response.status_code])
    if response.status_code in (400, 405, 422):
        raise TextTransportError('PROVIDER_REJECTED', f'文本服务拒绝请求（HTTP {response.status_code}），请检查模型、输入和思考模式兼容性')
    response.raise_for_status()


def receive_text(client, url, headers, payload, stream=False):
    try:
        if not stream:
            response = client.post(url, headers=headers, json=payload)
            check_status(response)
            choice = response.json()['choices'][0]
            if choice.get('finish_reason') in ('length', 'content_filter'):
                raise TextTransportError('TEXT_INCOMPLETE', '模型输出被长度限制或内容过滤截断，未采用不完整结果')
            return choice['message']['content']
        pieces, size, stopped = [], 0, False
        started = time.monotonic()
        with client.stream('POST', url, headers=headers, json={**payload, 'stream': True}) as response:
            check_status(response)
            response.encoding = 'utf-8'
            data = []
            for line in response.iter_lines():
                if time.monotonic() - started > 600:
                    raise TextTransportError('TEXT_TOTAL_TIMEOUT', '文本生成超过10分钟，已停止接收；服务商可能仍计费，请核查后手动重试')
                if line.startswith('data:'):
                    data.append(line[5:].lstrip())
                    continue
                if line or not data:
                    continue
                raw, data = '\n'.join(data), []
                if raw == '[DONE]':
                    break
                item = json.loads(raw)
                if item.get('error'):
                    raise TextTransportError('TEXT_STREAM_INTERRUPTED', '文本服务在流中返回错误，未采用部分结果；请核查服务商记录后重试')
                for choice in item.get('choices', []):
                    if choice.get('index', 0) != 0:
                        continue
                    finish = choice.get('finish_reason')
                    if finish and finish != 'stop':
                        raise TextTransportError('TEXT_INCOMPLETE', '模型输出被截断或未返回完整正文，请检查输出限制与模型能力')
                    stopped = stopped or finish == 'stop'
                    content = choice.get('delta', {}).get('content')
                    if content is not None:
                        if not isinstance(content, str):
                            raise ValueError('content type')
                        size += len(content)
                        if size > 2_000_000:
                            raise TextTransportError('TEXT_INCOMPLETE', '文本输出超过接收上限，未采用部分结果')
                        pieces.append(content)
            if not stopped or not ''.join(pieces).strip():
                raise TextTransportError('TEXT_STREAM_INTERRUPTED', '文本流未完整结束或仅返回思考内容，未采用部分结果；请核查服务商记录后手动重试')
        return ''.join(pieces)
    except httpx.ConnectTimeout as exc:
        raise TextTransportError('TEXT_CONNECT_TIMEOUT', '连接文本服务超时（15秒），请检查服务地址、网络和代理后手动重试') from exc
    except httpx.ReadTimeout as exc:
        raise TextTransportError('TEXT_READ_TIMEOUT', '等待文本服务内容超时（连续120秒未收到数据），可关闭思考或开启流式；服务商可能仍计费，请核查后手动重试') from exc
    except httpx.TransportError as exc:
        raise TextTransportError('TEXT_STREAM_INTERRUPTED', '文本服务连接中断，未采用部分结果；请检查网络并核查服务商记录后手动重试') from exc
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise TextTransportError('TEXT_RESPONSE_INVALID', '文本服务返回格式异常，未采用部分结果，请检查接口兼容性') from exc
