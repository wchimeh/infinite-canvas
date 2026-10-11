"""持久化调度。单个调度线程配合独立租约心跳，不阻塞 HTTP 服务。"""
import copy
import json
from concurrent.futures import ThreadPoolExecutor
import os
import random
import threading
import time
import uuid

from app.graph import DEFINITIONS, execution_order, node_kind, snapshot_hash, validate_graph
from app.providers import MockProvider, ProviderError, RunningHub, TextProvider
from app.credentials import Settings
from app.costs import BudgetLedger, quote_snapshot, summarize_quotes
from app.comfy import ComfyUI
from app.generation_profiles import TEXT_KINDS, resolve_selection, build_workflow_request
from app.shot_nodes import EXPANSION_VERSION, select_shot, validate_expansion_inputs


class Worker:
    def __init__(self, store, mock=False, settings=None):
        self.store = store
        self.mock = mock
        self.settings = settings or Settings()
        self.provider = MockProvider() if mock else RunningHub(settings=self.settings)
        self.ledger = BudgetLedger(store)
        self.owner = uuid.uuid4().hex
        self.stop_event = threading.Event()
        self.thread = None
        self.current = None
        self.heartbeat_thread = None
        self.active = set()
        self.active_lock = threading.Lock()
        self.pools = {}

    def submit(self, pid, selected=None, force=False, dry_run=False):
        canvas = self.store.canvas(pid)
        errors = validate_graph(canvas["nodes"], canvas["edges"])["errors"]
        if errors:
            raise ValueError("；".join(errors))
        forced_ids = set(selected or [n['id'] for n in canvas['nodes']]) if force else set()
        requested_ids = set(selected or [n['id'] for n in canvas['nodes']])
        forced_ids.update(n['id'] for n in canvas['nodes'] if n['id'] in requested_ids
                          and n['data'].get('config', {}).get('overwriteCache') is True
                          and (node_kind(n) in TEXT_KINDS or node_kind(n).startswith(('image.', 'video.', 'audio.'))))
        adopted_ids = {n['id'] for n in canvas['nodes'] if n['data'].get('config', {}).get('assetId') and n['id'] not in forced_ids}
        effective_edges = [e for e in canvas['edges'] if e['target'] not in adopted_ids]
        order = execution_order(canvas["nodes"], effective_edges, selected)
        if not order:
            raise ValueError("请先添加节点")
        by_id = {n["id"]: n for n in canvas["nodes"]}
        cloud_enabled = self.store.document(pid, "project")["settings"].get("cloudEnabled", False)
        settings = self.settings.load()
        specs = []
        resolved_outputs = {}
        requested_ids = set(selected or [n['id'] for n in canvas['nodes']])
        for nid in order:
            node = by_id[nid]
            kind = node_kind(node)
            config = copy.deepcopy(node["data"].get("config", {}))
            links = [e for e in effective_edges if e["target"] == nid and e.get("data", {}).get("kind") != "sequence"]
            if kind == 'video.image_to_video':
                links.sort(key=lambda edge: int(edge['targetHandle'][5:] or '1') if edge['targetHandle'] != 'text' else 0)
            def input_port(link):
                return DEFINITIONS[kind]['inputs'][link['targetHandle']]
            adopted = nid in adopted_ids
            local = kind in ('story.prompt', 'shots.select') or kind.startswith("asset.") or kind.endswith(".reference") or adopted
            provider_id = config.get('provider', 'text' if kind in TEXT_KINDS else 'runninghub')
            if provider_id not in ('runninghub', 'text', 'comfyui') or (kind in TEXT_KINDS and provider_id != 'text'):
                raise ValueError('节点类型与生成服务不匹配')
            if not local and not cloud_enabled and provider_id != 'comfyui' and not self.mock and not dry_run:
                raise ValueError("项目处于仅本地模式，请先开启云端生成")
            # 固定引用的版本和 hash；不存在或跨项目引用在入队之前拒绝。
            references = list(config.get("referenceIds", []))
            if config.get("assetId") and (local or adopted):
                references.append(config["assetId"])
            frozen = []
            for aid in references:
                a = self.store.asset(aid)
                if a["projectId"] != pid:
                    raise ValueError("不能引用其他项目的素材")
                if aid == config.get('assetId') and a['mime'].split('/')[0] not in DEFINITIONS[kind]['outputs'].values():
                    raise ValueError('绑定素材类型与节点输出类型不匹配')
                self.store.asset_path(aid)
                frozen.append({"id": aid, "sha256": a["sha256"], "mime": a["mime"]})
            if (kind.startswith("asset.") or kind.endswith(".reference")) and not config.get("assetId"):
                raise ValueError(f"{node['data'].get('title', nid)} 尚未绑定素材")
            if not local and not config.get("prompt", "").strip() and not any(e.get("targetHandle") == "text" for e in links):
                raise ValueError("生成节点需要提示词或文本输入")
            selection = resolve_selection(settings, kind, config) if not local else {}
            if selection.get('textServiceId') not in (None, 'legacy') and not self.mock and not dry_run and not self.settings.key(selection['textCredential']):
                raise ValueError('所选文本服务尚未配置密钥，请在设置中保存该服务的密钥')
            template = selection.get('cloudWorkflow')
            if template and not template.get('builtin'):
                for mapping in template.get('mappings', []):
                    port = mapping['source']
                    if port in ('image', 'video', 'audio') and mapping.get('required', True):
                        count = sum(ref['mime'].startswith(port + '/') for ref in frozen)
                        if not any(input_port(e) == port for e in links) and count <= mapping.get('index', 0):
                            raise ValueError(f'所选工作流缺少 {port} 输入，请绑定参考素材或连接上游节点')
            specs.append({"nodeId": nid, "deps": list(dict.fromkeys(e["source"] for e in links)), "snapshot": {
                "nodeId": nid, "kind": kind, "config": config, "references": frozen,
                "links": [{"source": e["source"], "port": input_port(e)} for e in links],
                "adapterVersion": f'{TextProvider.version}/{EXPANSION_VERSION}' if kind == 'prompt.video_expand' else TextProvider.version if kind in TEXT_KINDS or kind == 'shots.select' else ComfyUI.version if provider_id == 'comfyui' else self.provider.version,
                "textModel": settings['textModel'], "textEndpoint": settings['textApiBase'],
                "providerId": provider_id, "comfyEndpoint": settings['comfyUrl'] if provider_id == 'comfyui' else None,
                "workflow": copy.deepcopy(settings['comfyWorkflows'].get(kind)) if provider_id == 'comfyui' else None,
                "force": nid in forced_ids, "adopted": adopted,
                "pricing": copy.deepcopy(settings['pricing']),
                **selection,
            }})
            if provider_id == 'comfyui' and not local and not specs[-1]['snapshot']['workflow']:
                raise ValueError('该节点尚未配置本地 ComfyUI 工作流模板')
            specs[-1]['snapshot']['quote'] = quote_snapshot(specs[-1]['snapshot'], settings['pricing'])
            spec = specs[-1]
            if adopted:
                resolved_outputs[nid] = {'node_id': nid, 'output': {'assets': [config['assetId']]}}
            elif nid not in requested_ids and not spec['snapshot']['force']:
                if all(dep in resolved_outputs for dep in spec['deps']):
                    try:
                        _, _, key = self.inputs({'snapshot': spec['snapshot'], 'deps': []},
                                                dependency_outputs=resolved_outputs)
                        cached = self.store.cached(pid, key)
                    except (ValueError, ProviderError, OSError):
                        cached = None
                    if cached is not None:
                        spec['cachedOutput'], spec['cachedHash'] = cached, key
                        spec['snapshot']['quote'] = {**spec['snapshot']['quote'], 'known': True,
                                                     'amount': '0.000000', 'basis': 'cache'}
                        resolved_outputs[nid] = {'node_id': nid, 'output': cached}
        if dry_run:
            return {**summarize_quotes([spec['snapshot']['quote'] for spec in specs]), 'nodeIds': order}
        return self.store.create_run(pid, specs, force)

    def start(self):
        self.store.recover()
        self.pools = {queue: ThreadPoolExecutor(max_workers=8, thread_name_prefix='canvas-' + queue)
                      for queue in ('text', 'media', 'audio', 'local')}
        self.thread = threading.Thread(target=self.loop, name="canvas-worker", daemon=True)
        self.heartbeat_thread = threading.Thread(target=self.heartbeat, name="canvas-lease", daemon=True)
        self.thread.start()
        self.heartbeat_thread.start()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
        for pool in self.pools.values():
            pool.shutdown(wait=False, cancel_futures=True)

    def heartbeat(self):
        while not self.stop_event.wait(20):
            with self.active_lock:
                tasks = list(self.active)
            for tid in tasks:
                self.store.update_task(tid, expected="running", lease_until=time.time() + 180)

    def loop(self):
        futures = {queue: set() for queue in self.pools}
        while not self.stop_event.is_set():
            try:
                self.store.recover()
                capacities = self.settings.load()['concurrency']
                worked = False
                for queue, pool in self.pools.items():
                    futures[queue] = {future for future in futures[queue] if not future.done()}
                    if len(futures[queue]) >= 8:
                        continue
                    task = self.store.claim(self.owner, capacities=capacities, queue=queue)
                    if task:
                        futures[queue].add(pool.submit(self.tick, task))
                        worked = True
            except Exception:
                # 服务级异常只记录类型，不把提示词或凭据写入日志。
                import logging
                logging.getLogger(__name__).error("worker iteration failed")
                worked = False
            self.stop_event.wait(0.2 if worked else 1)

    def inputs(self, task, dependency_outputs=None):
        snap = task["snapshot"]
        dep_by_node = dependency_outputs if dependency_outputs is not None else {t["node_id"]: t for t in (self.store.task(i) for i in task["deps"])}
        input_ids, texts, hashes = {}, [], []
        selected_seconds = None
        for link in snap["links"]:
            output = dep_by_node[link["source"]]["output"]
            if link["port"] == "text":
                if snap['kind'] in ('prompt.video_expand', 'video.image_to_video') and 'seconds' in output:
                    selected_seconds = output['seconds']
                field = {'image.character': 'characters', 'image.location': 'locations'}.get(snap['kind'])
                if field and len(output.get(field, [])) > 1 and not task.get('external_id'):
                    label = '角色' if field == 'characters' else '场景'
                    raise ProviderError('MULTIPLE_SUBJECTS', f'上游包含多个{label}，单个图片节点只生成一张；请点击“生成全部{label}”拆分为独立节点后生成')
                texts.append(output.get("text", ""))
            else:
                input_ids.setdefault(link["port"], []).extend(output.get("assets", []))
            hashes.append({"port": link["port"], "output": output})
        for ref in snap["references"]:
            self.store.asset_path(ref["id"])
            if ref["id"] == snap["config"].get("assetId"):
                continue
            port = ref["mime"].split("/")[0]
            input_ids.setdefault(port, []).append(ref["id"])
        config = dict(snap["config"])
        config.pop('overwriteCache', None)
        config.pop('_workflow', None)
        config["prompt"] = "\n\n".join(t for t in [*texts, config.get("prompt", "")] if t)
        if selected_seconds is not None:
            if isinstance(selected_seconds, bool) or not isinstance(selected_seconds, (int, float)) or not 4 <= selected_seconds <= 15:
                raise ValueError('上游分镜时长必须为 4–15 秒')
            config['seconds'] = selected_seconds
        if snap['kind'] == 'image.character' and config['prompt'].strip():
            config['prompt'] += ('\n\n输出要求：同一张横向角色三视图设定图，左侧正面、中间侧面、右侧背面。'
                                 '三个视角均为同一个角色，全身完整、自然站立、等比例、等高度、同一服装与发型，'
                                 '面部、体型、配饰和材质保持一致。纯色简洁背景，均匀光照，不裁切头脚，不添加文字、水印或多余人物。')
        if snap['kind'] == 'image.location' and config['prompt'].strip():
            config['prompt'] += ('\n\n输出要求：同一张场景四视图设定图，2×2 四宫格。左上前视图、右上右视图、'
                                 '左下后视图、右下左视图，分别展示同一空间前、右、后、左四个方向。'
                                 '四个视角的建筑结构、门窗位置、主要道具、材质、时间与光照必须一致，保持空间关系合理。'
                                 '完整展示环境，四格等大，不要变成四个不同地点，不添加人物、文字、水印。')
        inputs = {}
        asset_hashes = {}
        if snap['kind'] == 'video.image_to_video':
            for port, limit in [('image', 9), ('audio', 3), ('video', 3)]:
                if len(input_ids.get(port, [])) > limit:
                    raise ValueError(f'生成视频最多支持 {limit} 个 {port} 参考素材，连线与勾选数量合计超限')
        for port, ids in input_ids.items():
            if snap['kind'] == 'prompt.video_expand' and (port != 'image' or len(ids) > 9):
                raise ValueError('视频提示词扩写只支持最多 9 张参考图片')
            inputs[port] = []
            asset_hashes[port] = []
            for aid in ids:
                path = self.store.asset_path(aid)
                a = self.store.asset(aid)
                if not a["mime"].startswith(port + "/"):
                    raise ValueError("输入素材类型与端口不匹配")
                inputs[port].append(path.read_bytes())
                asset_hashes[port].append({"revisionId": aid, "sha256": a["sha256"]})
        if snap['kind'] == 'prompt.video_expand':
            validate_expansion_inputs(config.get('seconds', 5), inputs.get('image', []))
        key = snapshot_hash({"kind": snap["kind"], "config": config, "inputs": asset_hashes,
                             "upstream": hashes, "adapter": snap["adapterVersion"],
                             "textModel": snap["textModel"], "textEndpoint": snap["textEndpoint"],
                             "providerId": snap.get('providerId'), 'workflow': snap.get('workflow'), 'comfyEndpoint': snap.get('comfyEndpoint'),
                             'cloudWorkflow': snap.get('cloudWorkflow'), 'textServiceId': snap.get('textServiceId')})
        if snap.get('cloudWorkflow'):
            config['_workflow'] = copy.deepcopy(snap['cloudWorkflow'])
        return config, inputs, key

    def tick(self, task=None):
        task = task or self.store.claim(self.owner, capacities=self.settings.load()['concurrency'])
        if not task:
            return False
        tid = task["id"]
        self.current = tid
        with self.active_lock:
            self.active.add(tid)
        pid = tid.split("_")[0]
        external_id = task["external_id"]
        submitting = False
        snap = task['snapshot']
        provider = self.provider if self.mock or snap.get('providerId') != 'comfyui' else ComfyUI(snap['comfyEndpoint'], {snap['kind']: snap['workflow']})
        try:
            # 用户采用的版本优先，且不能作为生成缓存供后续任务复用。
            if snap.get("adopted"):
                self.store.asset_path(snap["config"]["assetId"])
                self.store.update_task(tid, input_hash=None)
                self.finish(tid, {"assets": [snap["config"]["assetId"]]}, reused=True)
                return True
            config, inputs, key = self.inputs(task)
            self.store.update_task(tid, input_hash=key)
            kind = task["snapshot"]["kind"]
            local = kind in ('story.prompt', 'shots.select') or kind.startswith('asset.') or kind.endswith('.reference')
            if not local and not external_id and not config.get('prompt', '').strip():
                raise ProviderError('EMPTY_TEXT_INPUT', '没有可生成的文本，请在上游故事节点填写内容，或在当前节点填写提示词后重新运行')
            cached = None if task["snapshot"]["force"] or external_id else self.store.cached(pid, key)
            if cached is not None:
                self.finish(tid, cached, reused=True)
                return True
            if kind == "story.prompt":
                self.finish(tid, {"text": config.get("prompt", "")})
            elif kind == 'shots.select':
                deps = {self.store.task(dep)['node_id']: self.store.task(dep) for dep in task['deps']}
                sources = [deps[link['source']]['output'] for link in snap['links'] if link['port'] == 'text']
                if len(sources) != 1:
                    raise ValueError('请连接一个提取分镜节点并选择分镜')
                shots = sources[0].get('shots')
                if shots is None:
                    try:
                        shots = json.loads(sources[0].get('text', ''))
                    except ValueError as exc:
                        raise ValueError('上游没有分镜列表，请连接提取分镜节点并选择分镜') from exc
                self.finish(tid, select_shot(shots, config))
            elif kind.startswith("asset.") or kind.endswith(".reference"):
                self.store.asset_path(config["assetId"])
                self.finish(tid, {"assets": [config["assetId"]]})
            elif kind in TEXT_KINDS:
                if not self.mock:
                    if not self.store.document(pid, "project")["settings"].get("cloudEnabled"):
                        raise ProviderError("CLOUD_DISABLED", "云端生成已关闭，任务未提交")
                    quote = snap.get('quote')
                    if config.get('seconds') != snap['config'].get('seconds'):
                        quote = quote_snapshot({**snap, 'config': config}, snap.get('pricing', self.settings.load()['pricing']))
                    self.ledger.reserve(pid, tid, quote or quote_snapshot(snap, self.settings.load()['pricing']))
                    self.store.update_task(tid, submitted=1)
                    submitting = True
                if self.mock:
                    output = {'text': config.get('prompt', '')}
                else:
                    text_provider = TextProvider(self.settings, snap['textEndpoint'], snap['textModel'], credential=snap.get('textCredential', 'text'))
                    options = {'seconds': config.get('seconds', 5), 'images': inputs.get('image', [])} if kind == 'prompt.video_expand' else {}
                    output = text_provider.generate(kind, config.get('prompt', ''), **options)
                if kind == 'prompt.video_expand':
                    output['seconds'] = config.get('seconds', 5)
                submitting = False
                self.finish(tid, output)
            else:
                if not external_id:
                    if snap.get('cloudWorkflow') or (not self.mock and snap.get('providerId') != 'comfyui'):
                        build_workflow_request(kind, config, inputs, snap.get('cloudWorkflow'))
                    if not self.mock and snap.get('providerId') != 'comfyui' and not self.store.document(pid, "project")["settings"].get("cloudEnabled"):
                        raise ProviderError("CLOUD_DISABLED", "云端生成已关闭，任务未提交")
                    if not self.mock:
                        quote = snap.get('quote')
                        if config.get('seconds') != snap['config'].get('seconds'):
                            quote = quote_snapshot({**snap, 'config': config}, snap.get('pricing', self.settings.load()['pricing']))
                        self.ledger.reserve(pid, tid, quote or quote_snapshot(snap, self.settings.load()['pricing']))
                    task['deadline_at'] = time.time() + 7200
                    self.store.update_task(tid, submitted=1, deadline_at=task['deadline_at'])
                    submitting = True
                    external_id = provider.submit(kind, config, inputs)
                    self.store.update_task(tid, external_id=external_id)
                    submitting = False
                if self.store.task(tid)["status"] == "cancel_requested":
                    self.store.update_task(tid, status="cancelled", lease_until=0)
                    return True
                if time.time() > (task.get('deadline_at') or task['created_at'] + 7200):
                    raise ProviderError("TASK_TIMEOUT", "任务超过两小时，远端任务可能仍在运行，可重试查询")
                status = provider.poll(external_id)
                if status in ("QUEUED", "RUNNING"):
                    self.store.update_task(tid, expected="running", status="queued", next_poll=time.time() + 3, lease_until=0)
                elif status == "FAILED":
                    raise ProviderError("PROVIDER_TASK_FAILED", "云端生成失败，请检查提示词、参考素材和工作流")
                else:
                    files = provider.fetch(external_id, kind, config, inputs)
                    assets = [self.store.add_asset(pid, data, name, task["node_id"], task["run_id"])["id"] for data, name in files]
                    self.finish(tid, {"assets": assets})
        except ProviderError as exc:
            if submitting and exc.code in ('PROVIDER_AUTH', 'PROVIDER_REJECTED', 'PROVIDER_RATE_LIMIT', 'INVALID_INPUT', 'MODEL_UNAVAILABLE', 'OUT_OF_CREDITS', 'LOCAL_MODEL_REJECTED'):
                self.ledger.release(pid, tid, '服务拒绝提交')
            if submitting and exc.code in ("PROVIDER_NETWORK", "PROVIDER_UNAVAILABLE", "PROVIDER_MALFORMED", "SUBMIT_UNCERTAIN", "TEXT_GENERATION_FAILED"):
                self.store.update_task(tid, expected="running", status="failed", error_code="SUBMIT_UNCERTAIN", error="提交结果不确定，请核查服务商任务和账单后手动重试", retryable=0)
            elif exc.retryable and not submitting and task["attempt"] < 4:
                self.store.update_task(tid, expected="running", status="queued", attempt=task["attempt"] + 1,
                                       error=str(exc), error_code=exc.code, next_poll=time.time() + 2 ** (task["attempt"] + 1) + random.random(), lease_until=0)
            else:
                self.store.update_task(tid, expected="running", status="failed", error=str(exc), error_code=exc.code, retryable=exc.retryable, lease_until=0)
        except (ValueError, KeyError) as exc:
            self.store.update_task(tid, expected="running", status="failed", error=str(exc), error_code="INVALID_INPUT", lease_until=0)
        except Exception:
            self.store.update_task(tid, expected="running", status="failed", error="提交结果不确定，请核查服务商账单" if submitting else "本地处理失败，请检查磁盘空间及素材后重试", error_code="SUBMIT_UNCERTAIN" if submitting else "LOCAL_FAILURE", lease_until=0)
        finally:
            if self.store.task(tid)["status"] == "cancel_requested":
                self.store.update_task(tid, status="cancelled", lease_until=0)
            self.current = None
            with self.active_lock:
                self.active.discard(tid)
        return True

    def finish(self, tid, output, reused=False):
        # CAS：取消发生在下载/写盘期间，结果保留为历史素材，但不自动采用。
        self.store.update_task(tid, expected="running", status="completed", output=output, reused=reused, error=None, error_code=None, lease_until=0)

    def retry(self, tid, confirm_uncertain=False):
        # 同一事务归档历史费用并重排队，防止并发重试或崩溃复用旧收费预留。
        with self.store.db(tid) as con:
            con.execute('BEGIN IMMEDIATE')
            task = con.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
            if not task or task['status'] not in ('failed', 'blocked', 'cancelled'):
                raise ValueError('只能重试已停止的任务')
            if task['error_code'] == 'SUBMIT_UNCERTAIN' and not confirm_uncertain:
                raise ValueError('请先核查云端账单并确认是否重新提交，避免重复计费')
            keep_remote = bool(task['external_id']) and task['error_code'] != 'PROVIDER_TASK_FAILED'
            self.ledger.ensure(con)
            if not keep_remote and task['submitted']:
                con.execute("UPDATE cost_reservations SET task_id=?,reason=? WHERE task_id=? AND status='reserved'",
                            (tid + '#previous-' + uuid.uuid4().hex, '重新提交前保留上次可能收费记录', tid))
            now = time.time()
            con.execute("UPDATE tasks SET status='queued',error=NULL,error_code=NULL,attempt=0,external_id=?,submitted=?,next_poll=0,lease_until=0,updated_at=?,deadline_at=? WHERE id=?",
                        (task['external_id'] if keep_remote else None, int(keep_remote), now, now + 7200 if keep_remote else None, tid))
            self.store.event(con, {'event': 'task.updated', 'taskId': tid, 'status': 'queued',
                                  'projectId': tid.split('_')[0], 'runId': task['run_id'], 'nodeId': task['node_id']})
        return self.store.task(tid)
