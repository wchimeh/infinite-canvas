"""云服务适配；不向前端暴露凭据或上游原始错误体。"""
import io
import base64
import json
import os
import secrets
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageDraw

from generate_tool.rh_generate_workflow import build_request
from generate_tool import rh_process_generate
from app.credentials import Settings
from app.generation_profiles import build_workflow_request, generation_options
from app.shot_nodes import expansion_instruction, validate_expansion, validate_expansion_inputs


class ProviderError(Exception):
    def __init__(self, code, message, retryable=False):
        super().__init__(message)
        self.code, self.retryable = code, retryable


class RunningHub:
    version = "runninghub-2"

    def __init__(self, key=None, client=None, settings=None):
        self.settings = settings or Settings()
        self.explicit_key = key
        self.client = client or httpx.Client(timeout=httpx.Timeout(120, connect=15), follow_redirects=False)
        self.base = "https://www.runninghub.cn/task/openapi/"

    @property
    def key(self):
        return self.explicit_key if self.explicit_key is not None else self.settings.key('runninghub')

    def request(self, endpoint, payload=None, files=None):
        if not self.key:
            raise ProviderError("PROVIDER_AUTH", "未配置 RUNNINGHUB_API_KEY")
        try:
            if files:
                response = self.client.post(self.base + endpoint, data={"apiKey": self.key}, files=files)
            else:
                response = self.client.post(self.base + endpoint, json={"apiKey": self.key, **(payload or {})})
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_NETWORK", "云端连接中断，请稍后检查任务状态", True) from exc
        if response.status_code in (401, 403):
            raise ProviderError("PROVIDER_AUTH", "云端身份验证失败，请检查密钥和工作流权限")
        if response.status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMIT", "云端限流，稍后重试", True)
        if response.status_code >= 500:
            raise ProviderError("PROVIDER_UNAVAILABLE", "云端服务暂不可用", True)
        if not response.is_success:
            raise ProviderError("PROVIDER_REJECTED", f"云端拒绝请求（HTTP {response.status_code}）")
        try:
            body = response.json()
            code = body.get("code")
            if code != 0:
                message = str(body.get("msg", body.get("message", ""))).lower()
                if any(x in message for x in ("balance", "credit", "余额", "积分")):
                    raise ProviderError("OUT_OF_CREDITS", "云端额度不足，请充值后重试")
                if any(x in message for x in ("key", "auth", "token")):
                    raise ProviderError("PROVIDER_AUTH", "云端密钥或权限无效")
                if any(x in message for x in ("queue", "limit", "频繁")):
                    raise ProviderError("PROVIDER_RATE_LIMIT", "云端队列繁忙，请稍后重试", True)
                raise ProviderError("PROVIDER_REJECTED", f"云端拒绝请求（业务码 {code}），请检查工作流权限及参数")
            return body.get("data")
        except (ValueError, AttributeError) as exc:
            raise ProviderError("PROVIDER_MALFORMED", "云端返回了无法解析的响应") from exc

    def submit(self, kind, config, inputs):
        request = build_workflow_request(kind, config, inputs, config.get('_workflow'))
        nodes = request["nodeInfoList"]
        for n in nodes:
            if (not config.get('_workflow') or config['_workflow'].get('builtin')) and n["fieldName"] in ("seed", "noise_seed"):
                n["fieldValue"] = str(secrets.randbelow(2147483647))
        for item in request["user_data"]:
            entry = dict(item)
            media_type = entry.pop('_mediaType', None)
            if isinstance(entry["fieldValue"], bytes):
                field = media_type or entry["fieldName"]
                filename, mime = {"image": ("input.png", "image/png"), "video": ("input.mp4", "video/mp4"), "audio": ("input.wav", "audio/wav")}[field]
                data = self.request("upload", files={"file": (filename, entry["fieldValue"], mime)})
                if not isinstance(data, dict) or not data.get("fileName"):
                    raise ProviderError("UPLOAD_FAILED", "参考素材上传失败")
                entry["fieldValue"] = data["fileName"]
            nodes.append(entry)
        if 'workflow' in request:
            graph = request['workflow']
            for entry in nodes:
                graph[entry['nodeId']]['inputs'][entry['fieldName']] = entry['fieldValue']
            task_id = rh_process_generate.rh_api_generate_by_workflow(
                graph, request.get('workflowId'), request=self.request)
            data = {'taskId': task_id}
        else:
            data = self.request("create", {"workflowId": request["workflowId"], "nodeInfoList": nodes})
        if not isinstance(data, dict) or not data.get("taskId"):
            raise ProviderError("SUBMIT_UNCERTAIN", "云端未返回任务 ID，请核查云端任务后重试")
        return str(data["taskId"])

    def poll(self, external_id):
        status = self.request("status", {"taskId": external_id})
        if status not in ("QUEUED", "RUNNING", "FAILED", "SUCCESS"):
            raise ProviderError("PROVIDER_MALFORMED", "云端返回未知任务状态")
        return status

    def fetch(self, external_id, kind, config, inputs):
        result_nodes = build_workflow_request(kind, config, inputs, config.get('_workflow'))["result_node"]
        records = self.request("outputs", {"taskId": external_id})
        if not isinstance(records, list):
            raise ProviderError("PROVIDER_MALFORMED", "云端输出格式错误")
        results = []
        for record in records:
            if str(record.get("nodeId")) not in result_nodes:
                continue
            url = str(record.get("fileUrl", ""))
            parsed = urlparse(url)
            # 输出只接受服务商的 HTTPS 媒体域，避免响应 URL 访问本地网络。
            if parsed.scheme != "https" or not parsed.hostname or not any(parsed.hostname == h or parsed.hostname.endswith("." + h) for h in ("runninghub.cn", "runninghub.ai", "xiaoyaoyou.com")):
                raise ProviderError("PROVIDER_MALFORMED", "云端返回了未允许的素材域名")
            ext = str(record.get("fileType", "")).lower().lstrip(".")
            if ext not in {"png", "jpg", "jpeg", "webp", "mp4", "webm", "wav", "mp3", "m4a", "ogg", "flac"}:
                raise ProviderError("PROVIDER_MALFORMED", "云端返回了不支持的文件类型")
            try:
                with self.client.stream("GET", url) as response:
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 512 * 1024 * 1024:
                            raise ProviderError("ASSET_TOO_LARGE", "云端素材超过 512 MB")
                        chunks.append(chunk)
                results.append((b"".join(chunks), f"{external_id}.{ext}"))
            except httpx.HTTPError as exc:
                raise ProviderError("PROVIDER_NETWORK", "生成成功，但下载素材失败，可重试下载", True) from exc
        if not results:
            raise ProviderError("PROVIDER_EMPTY", "云端任务未产生预期节点的输出")
        return results


class TextProvider:
    version = "text-7"

    def __init__(self, settings=None, base=None, model=None, credential='text'):
        self.settings = settings or Settings()
        self.base, self.model = base, model
        self.credential = credential

    def generate(self, kind, prompt, *, seconds=5, images=None):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ProviderError('EMPTY_TEXT_INPUT', '没有可生成的文本，请在上游故事节点填写内容，或在当前节点填写提示词后重新运行')
        config = self.settings.load()
        base = self.base if self.base is not None else config['textApiBase']
        model = self.model if self.model is not None else config['textModel']
        key = self.settings.key(self.credential)
        if not all((base, key, model)):
            raise ProviderError("MODEL_UNAVAILABLE", "请配置文本服务地址、密钥和模型，或手动编辑剧本")
        instruction = ("你是中文短剧编剧。用户输入可能是一句话创意、故事梗概或完整故事，都是有效创作素材。"
                       "请直接据此创作完整的短剧片段，包含场景、人物动作、冲突和对白。"
                       "如果只有一句话，围绕核心创意合理补全角色、背景、情节和结局，不要要求用户先提供完整故事、角色或对白。"
                       "已有的人物设定和情节应保留，遵守用户补充的篇幅、风格等要求。只输出剧本正文，不输出索要素材的说明。")
        if kind == "shots.extract":
            instruction = ('将用户提供的故事、简短梗概或完整剧本直接拆分为 3–5 个连贯分镜。'
                           '每条分镜时长必须为 4–15 秒，动作和对白必须能在该时长内完成。'
                           '简短梗概也足够，请合理补全画面动作，不要追问用户提供完整剧本。'
                           '保留已有角色、情节和对白；没有对白时 dialogue 使用空字符串。'
                           '只返回 JSON 数组，不加说明或代码围栏；每项含 title、visualPrompt、dialogue（字符串）、'
                           'durationMs（4000–15000 的整数）、shotSize、cameraMove。')
        if kind == 'character.extract':
            instruction = ('从用户提供的故事或剧本中提取主要角色。简短梗概也有效，可合理补全必要的角色设定，'
                           '不要要求用户提供完整剧本。只返回 JSON 数组，不加说明；每个角色包含 name（非空姓名或称谓）、'
                           'description（身份与性格）、appearance（稳定外貌特征）、wardrobe（服装）、restrictions（需避免的特征），'
                           '这些字段均为字符串，无内容用空字符串。最多 20 个角色，区分不同人物，不重复同一角色。')
        if kind == 'location.extract':
            instruction = ('从用户的故事、简短梗概或剧本中提取可复用的场景环境。简短输入可合理补全，不要追问完整剧本。'
                           '按地点去重，不按剧情场次重复列出；只返回 JSON 数组，最多 20 项。'
                           '每项包含 name（非空场景名）、description（环境、时间、光照与美术风格）、'
                           'layout（空间结构、门窗、建筑和主要道具位置）、restrictions（需避免的环境元素），'
                           '字段全部是字符串，未指定用空字符串。只写环境，不把人物外貌当作场景。')
        if kind == 'prompt.video_expand':
            try:
                validate_expansion_inputs(seconds, images or [])
            except ValueError as exc:
                raise ProviderError('INVALID_INPUT', str(exc)) from exc
            try:
                instruction = expansion_instruction()
            except OSError as exc:
                raise ProviderError('MODEL_UNAVAILABLE', '视频提示词规范 ref-en.txt 无法读取，请检查安装文件') from exc
            prompt += f'\n\nTarget duration: {seconds:g} seconds. Fit all actions and dialogue within this duration.'
        user_content = prompt
        try:
            if kind == 'prompt.video_expand' and images:
                user_content = [{'type': 'text', 'text': prompt}]
                for index, data in enumerate(images):
                    with Image.open(io.BytesIO(data)) as reference:
                        reference.thumbnail((2048, 2048))
                        output = io.BytesIO()
                        reference.convert('RGB').save(output, format='JPEG', quality=90)
                    encoded = base64.b64encode(output.getvalue()).decode('ascii')
                    user_content.extend([{'type': 'text', 'text': f'<Picture {index + 1}> (reference image {index + 1})'},
                                         {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + encoded}}])
            with httpx.Client(timeout=120) as client:
                response = client.post(base.rstrip("/") + "/chat/completions", headers={"Authorization": "Bearer " + key}, json={"model": model, "messages": [{"role": "system", "content": instruction}, {"role": "user", "content": user_content}]})
                if response.status_code in (401, 403):
                    raise ProviderError('PROVIDER_AUTH', '文本服务身份验证失败，请检查此服务的密钥和模型权限后重试')
                if response.status_code == 404:
                    raise ProviderError('MODEL_UNAVAILABLE', '文本服务地址或模型不存在，请修正配置后重新运行节点')
                if response.status_code == 429:
                    raise ProviderError('PROVIDER_RATE_LIMIT', '文本服务限流，请稍后手动重试', True)
                if response.status_code in (400, 405, 422):
                    raise ProviderError('PROVIDER_REJECTED', f'文本服务拒绝请求（HTTP {response.status_code}），请检查地址、模型及输入后重新运行节点')
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("empty")
            if kind == 'prompt.video_expand':
                try:
                    return {'text': validate_expansion(text), 'seconds': seconds}
                except ValueError as exc:
                    raise ProviderError('TEXT_FORMAT_INVALID', '扩写结果未按参考规范返回六段内容，请重新扩写') from exc
            if kind in ('character.extract', 'location.extract'):
                clean = text.strip()
                if clean.startswith('```'):
                    clean = clean.split('\n', 1)[1].rsplit('```', 1)[0]
                characters = json.loads(clean)
                if not isinstance(characters, list) or not 1 <= len(characters) <= 20:
                    raise ValueError('characters')
                normalized, names = [], set()
                for item in characters:
                    if not isinstance(item, dict):
                        raise ValueError('character schema')
                    character = {}
                    fields = ('name', 'description', 'layout', 'restrictions') if kind == 'location.extract' else ('name', 'description', 'appearance', 'wardrobe', 'restrictions')
                    for field in fields:
                        value = item.get(field, '')
                        if not isinstance(value, str) or len(value) > (100 if field == 'name' else 4000):
                            raise ValueError('character field')
                        character[field] = value.strip()
                    name = character['name'].casefold()
                    if not name or name in names:
                        raise ValueError('character name')
                    names.add(name); normalized.append(character)
                return {'text': encode_text(normalized), 'locations' if kind == 'location.extract' else 'characters': normalized}
            if kind == "shots.extract":
                clean = text.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
                shots = json.loads(clean)
                if not isinstance(shots, list) or not 1 <= len(shots) <= 50:
                    raise ValueError("shots")
                for shot in shots:
                    if (not isinstance(shot, dict) or not isinstance(shot.get("visualPrompt"), str)
                            or type(shot.get("durationMs")) is not int or not 4000 <= shot["durationMs"] <= 15000):
                        raise ValueError("shot schema")
                return {"text": encode_text(shots), "shots": shots}
            return {"text": text}
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("TEXT_GENERATION_FAILED", "文本服务请求失败或返回内容不符合格式；请检查配置后重试") from exc


def encode_text(value):
    return json.dumps(value, ensure_ascii=False)


class MockProvider:
    """仅注入自动测试；不出现在正常 UI 的模型列表。"""
    version = "mock-1"

    def submit(self, kind, config, inputs):
        return "mock-" + secrets.token_hex(8)

    def poll(self, external_id):
        return "SUCCESS"

    def fetch(self, external_id, kind, config, inputs):
        out = io.BytesIO()
        image = Image.new("RGB", (320, 480), "#25435b")
        ImageDraw.Draw(image).text((30, 210), "MOCK TEST ASSET", fill="white")
        image.save(out, "PNG")
        return [(out.getvalue(), "mock.png")]


def capabilities(settings=None):
    settings = settings or Settings()
    config = settings.load()
    text_services = generation_options(settings)['textServices']
    return [
        {"id": "runninghub", "name": "RunningHub", "ready": bool(settings.key('runninghub')), "modalities": ["image", "video", "audio"], "models": ["Image2.0", "ltx23", "wan22", "Qwen TTS", "VoxCPM2", "MMAudio"], "maxReferenceImages": 8, "cancelSupported": False, "pricing": None},
        {"id": "text", "name": "文本服务", "ready": any(s['ready'] for s in text_services), "modalities": ["text"], "models": [s['name'] + ' / ' + m for s in text_services if s['enabled'] for m in s['models']], "pricing": None},
        {"id": "comfyui", "name": "本地 ComfyUI", "ready": bool(config['comfyWorkflows']), "modalities": ["image", "video", "audio"], "models": list(config['comfyWorkflows']), "pricing": 0, "cancelSupported": False, "requiresHealthCheck": True},
    ]
