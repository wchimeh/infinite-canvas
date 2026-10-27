import { Settings2, Play, Check, Film, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { TextResultEditor } from './TextResultEditor';
import { FrameExtraction } from './FrameExtraction';
import { connectedImageIds } from './imageReferenceSelection';
import { BatchGeneration } from './BatchGeneration';
import { VideoDuration } from './VideoDuration';
import { MiniMaxSettings } from './MiniMaxSettings';
import { CombatVideoSettings } from './CombatVideoSettings';
import { ShotSelection } from './ShotSelection';
import { useStudio } from './store';
import { mediaUrl, thumbnailUrl } from './api';
import { STATUS, type Asset, type Config, type GenerationOptions, type Shot, type CharacterDraft, type LocationDraft, type PeopleDoc } from './types';

export function Inspector({ people, run, addClip, importShots, importCharacters, adoptCharacterImage, importLocations, adoptLocationImage, generationOptions, runStage }: { people: PeopleDoc; run: (ids: string[], force?: boolean) => void; addClip: (asset: Asset, title: string, seconds: number) => void; importShots: (shots: Shot[]) => void; importCharacters: (characters: CharacterDraft[], taskId: string, generate?: boolean, generationConfig?: Config) => void; adoptCharacterImage: (characterId: string, assetId: string) => void; importLocations: (locations: LocationDraft[], taskId: string, generate?: boolean, generationConfig?: Config) => void; adoptLocationImage: (locationId: string, assetId: string) => void; generationOptions: GenerationOptions; runStage: string }) {
  const [compare, setCompare] = useState<string[]>([]);
  const [referenceNotice, setReferenceNotice] = useState<{ id: string; text: string }>();
  const [videoMetadata, setVideoMetadata] = useState<{ id: string; seconds: number }>();
  const s = useStudio();
  const node = s.nodes.find(n => n.selected);
  if (!node) return <aside className="inspector"><div className="panel-title"><Settings2 size={15}/>镜头属性</div><div className="inspector-empty"><Settings2 size={30} strokeWidth={1}/><h3>选择一个节点</h3><p>编辑内容、绑定参考素材，<br/>查看生成记录与候选版本。</p></div><div className="workflow-guide"><span className="eyebrow">创作路径</span><p>故事文本 → 分镜图 → 视频</p><p>配音与字幕 → 时间线 → 成片</p><small>连线定义生成依赖，时间线定义镜头顺序。</small></div></aside>;
  const config = node.data.config;
  const kind = node.data.kind;
  const isVideoGeneration = ['video.image_to_video', 'video.combat'].includes(kind);
  const wiredImageIds = connectedImageIds(node.id, s.nodes, s.edges, s.definitions, s.tasks);
  const rawTask = s.tasks.find(t => t.node_id === node.id);
  const task: typeof rawTask = rawTask ? { ...rawTask, output: config.editedResult ?? (rawTask.snapshot.config.editedResult ? config.originalResult : undefined) ?? rawTask.output } : undefined;
  const candidates = s.assets.filter(a => a.nodeId === node.id);
  const current = s.assets.find(a => a.id === (config.assetId || task?.output.assets?.[0]));
  const videoSeconds = current && videoMetadata?.id === current.id ? videoMetadata.seconds : undefined;
  const patch = (value: Partial<Config>) => s.patch(node.id, { config: { ...config, ...value } });
  const isReference = kind.endsWith('.reference') || kind.startsWith('asset.');
  const textResult = task?.output.text;
  const busy = !!task && ['queued', 'running', 'cancel_requested'].includes(task.status);
  const isSelection = kind === 'shots.select';
  const isConcat = kind === 'text.concat';
  const isVideoTrim = kind === 'video.trim';
  const isTrim = kind === 'audio.trim' || isVideoTrim;
  const trimMedia = isVideoTrim ? '视频' : '音频';
  const isFrame = kind === 'frame.extract';
  const isExtraction = kind === 'audio.extract' || isTrim || isFrame;
  const trimStart = typeof config.trimStart === 'number' ? config.trimStart : 0;
  const trimEnd = typeof config.trimEnd === 'number' ? config.trimEnd : undefined;
  const trimInvalid = isTrim && (!Number.isFinite(trimStart) || trimStart < 0 || (trimEnd !== undefined && (!Number.isFinite(trimEnd) || trimEnd <= trimStart)));
  const hasReferenceAudio = kind === 'audio.tts' && (!!config.referenceIds?.some(id => s.assets.some(asset => asset.id === id && asset.mime.startsWith('audio/')))
    || s.edges.some(edge => edge.target === node.id && edge.targetHandle === 'audio' && edge.data?.kind !== 'sequence'));
  const separator = typeof config.separator === 'string' ? config.separator : '\n';
  const separatorMode = config.separatorMode === 'custom' ? 'custom' : separator === '\n' ? 'newline' : separator === ' ' ? 'space' : separator === '' ? 'none' : 'custom';
  const isText = ['script.expand', 'shots.extract', 'character.extract', 'location.extract', 'prompt.video_expand'].includes(kind);
  const availableWorkflows = generationOptions.workflows.filter(w => w.kinds.includes(kind));
  const selectedWorkflow = availableWorkflows.find(w => w.id === (config.workflowId || (kind === 'video.combat' ? 'builtin-minimax-h3-combat' : isVideoGeneration ? 'builtin-minimax-h3' : '')));
  const videoWorkflowMissing = isVideoGeneration && config.provider !== 'comfyui' && !selectedWorkflow?.enabled;
  const serviceId = config.textServiceId || 'legacy';
  const selectedService = generationOptions.textServices.find(s => s.id === serviceId);
  const selectedModel = serviceId === 'legacy' ? selectedService?.defaultModel || '' : config.textModel || selectedService?.defaultModel || '';
  const upstreamIds = s.edges.filter(edge => edge.target === node.id && edge.targetHandle === 'text' && edge.data?.kind !== 'sequence').map(edge => edge.source);
  const durationSource = kind === 'prompt.video_expand' ? s.nodes.find(item => upstreamIds.includes(item.id) && ['shots.select', 'prompt.video_expand'].includes(item.data.kind)) : undefined;
  const inheritedSeconds = durationSource?.data.kind === 'shots.select' ? (durationSource.data.config.selectedShot?.durationMs ?? 0) / 1000 : durationSource?.data.config.seconds ?? 5;
  const rawUpstreamTask = s.tasks.filter(t => upstreamIds.includes(t.node_id)).sort((a, b) => b.created_at - a.created_at)[0];
  const upstreamConfig = s.nodes.find(n => n.id === rawUpstreamTask?.node_id)?.data.config;
  const upstreamTask = rawUpstreamTask ? { ...rawUpstreamTask, output: upstreamConfig?.editedResult ?? rawUpstreamTask.output } : undefined;
  const selectionInvalid = isSelection && (upstreamTask?.status !== 'completed'
    || s.nodes.some(item => upstreamIds.includes(item.id) && item.data.status === 'dirty')
    || config.shotIndex === undefined || !config.selectedShot
    || JSON.stringify(upstreamTask?.output.shots?.[config.shotIndex]) !== JSON.stringify(config.selectedShot));
  const characterSource = kind === 'character.extract' ? task : kind === 'image.character' ? upstreamTask : undefined;
  const locationSource = kind === 'location.extract' ? task : kind === 'image.location' ? upstreamTask : undefined;
  return <aside className="inspector" key={node.id}>
    <div className="panel-title"><Settings2 size={15}/>节点属性<span className="muted">{s.definitions[kind]?.displayName}</span></div>
    <div className="inspector-scroll">
    {isConcat && <section className="inspector-section">
      <label>分隔方式<select aria-label="文本分隔方式" value={separatorMode} onChange={e => patch({ separatorMode: e.target.value, separator: ({ newline: '\n', space: ' ', none: '' } as Record<string, string>)[e.target.value] ?? separator })}>
        <option value="newline">换行</option><option value="space">空格</option><option value="none">直接拼接</option><option value="custom">自定义</option>
      </select></label>
      {separatorMode === 'custom' && <label>自定义分隔符<textarea aria-label="自定义分隔符" rows={2} value={separator} onChange={e => patch({ separator: e.target.value })}/></label>}
      <p className="muted">按文本 1–10 的连接点顺序拼接，连接后自动显示下一个输入口。保留原文空白和空段；仅在本机处理，不调用模型。</p>
    </section>}
      <label>名称<input value={node.data.title} onChange={e => s.patch(node.id, { title: e.target.value })}/></label>
      {Object.values(s.definitions[kind]?.inputs || {}).includes('image') && <section className="inspector-section">
        <button disabled={busy || !!runStage} onClick={() => {
          try { const count = s.inheritReferenceImages(node.id); setReferenceNotice({ id: node.id, text: `已连接 ${count} 张上游参考图，可撤销本次操作` }); }
          catch (error) { setReferenceNotice({ id: node.id, text: error instanceof Error ? error.message : '连接失败' }); }
        }}>连接上游参考图</button>
        <small>按上游顺序自动连线，替换当前图片参考；保留音频、视频参考。勾选的上游图片会创建或复用素材节点。</small>
        {referenceNotice?.id === node.id && <p role="status">{referenceNotice.text}</p>}
      </section>}
      {(isText || isSelection || kind === 'story.prompt' || kind.startsWith('image.') || kind.startsWith('video.')) && !isReference && !isTrim && <label>画面风格<select aria-label="画面风格" value={config.visualStyle || ''} onChange={e => patch({ visualStyle: e.target.value as Config['visualStyle'] })}>
        <option value="">自动继承上游（无上游时遵循原文）</option>
        <option value="live_action">真人实拍</option><option value="anime">二维动漫</option><option value="animation_3d">三维动画</option>
      </select><small>从故事或剧本开始选择，沿连接传递到角色、场景、分镜及生成节点。当前节点明确选择时覆盖上游。真人风格仍需搭配适合写实的工作流和参考图；已有结果需重新生成。</small></label>}
      {characterSource?.status === 'completed' && !!characterSource.output.characters?.length && <BatchGeneration key={`${node.id}:${characterSource.id}`} kind="image.character" count={characterSource.output.characters.length} taskId={characterSource.id} profiles={people.characters} initialConfig={kind === 'image.character' ? config : { visualStyle: config.visualStyle }} options={generationOptions} busy={busy} runStage={runStage} generate={selection => importCharacters(characterSource.output.characters!, characterSource.id, true, selection)}/>}
      {locationSource?.status === 'completed' && !!locationSource.output.locations?.length && <BatchGeneration key={`${node.id}:${locationSource.id}`} kind="image.location" count={locationSource.output.locations.length} taskId={locationSource.id} profiles={people.locations} initialConfig={kind === 'image.location' ? config : { visualStyle: config.visualStyle }} options={generationOptions} busy={busy} runStage={runStage} generate={selection => importLocations(locationSource.output.locations!, locationSource.id, true, selection)}/>}
      {isSelection && <><ShotSelection nodeId={node.id}/><small>本地选择，不调用大模型；输出所选分镜的画面、对白、镜头和时长。</small></>}
      {kind === 'audio.extract' && <p className="muted">连接一个视频素材或生成视频的输出，在本地提取第一条音轨为 WAV 音频。无需提示词、模型或云端工作流，不产生生成费用。原视频保持不变；无音轨的视频无法提取。结果可试听、接入音频参考或在时间线添加。</p>}
      {isFrame && <FrameExtraction nodeId={node.id} busy={busy || !!runStage} run={run}/>}
      {isTrim && <fieldset disabled={busy || !!runStage}><legend>{trimMedia}裁剪区间</legend>
        <label>开始时间（秒）<input aria-label="开始时间（秒）" type="number" min={0} step="any" value={trimStart} onChange={e => patch({ trimStart: e.target.value === '' ? 0 : Number(e.target.value) })}/></label>
        <label>结束时间（秒）<input aria-label="结束时间（秒）" type="number" min={0} step="any" placeholder="留空截取到末尾" value={trimEnd ?? ''} onChange={e => patch({ trimEnd: e.target.value === '' ? undefined : Number(e.target.value) })}/></label>
        {trimInvalid ? <p role="alert">开始时间不能小于 0，结束时间必须大于开始时间。</p> : <small>{trimEnd === undefined ? `从 ${trimStart} 秒截取到${trimMedia}末尾` : `截取时长：${Number((trimEnd - trimStart).toFixed(6))} 秒`}</small>}
        <p className="muted">{isVideoTrim ? '连接一个视频素材或视频输出。本地精确截取为 MP4，保留第一条音轨；无音轨也可裁剪。时间支持小数，超出原视频长度会提示。原素材不变，不产生云端费用。' : '连接一个音频素材、提取音频或其它音频输出。时间支持小数，运行时检查是否超出原音频长度。本地输出新的 WAV 音频，原素材不变，不产生云端费用。'}</p>
      </fieldset>}
      {!isReference && !isSelection && !isConcat && !isExtraction && <label>{kind === 'audio.tts' ? '对白 / 声音描述' : kind === 'story.prompt' ? '故事内容' : kind === 'prompt.video_expand' ? '补充要求 / 参考说明' : '提示词'}<textarea rows={8} value={config.prompt || ''} placeholder={kind === 'prompt.video_expand' ? '连接所选分镜，可补充参考图片角色、场景、风格和保留要求…' : '描述角色、场景、动作与镜头语言…'} onChange={e => patch({ prompt: e.target.value })}/></label>}
      {isText && <fieldset className="generation-choice"><legend>文本生成</legend>
        <label>文本服务商<select aria-label="文本服务商" value={serviceId} onChange={e => { const service = generationOptions.textServices.find(s => s.id === e.target.value); patch({ textServiceId: e.target.value, textModel: service?.defaultModel || '' }); }}>
          {!selectedService && <option value={serviceId}>原服务已失效，请重新选择</option>}
          {generationOptions.textServices.map(service => <option key={service.id} value={service.id} disabled={!service.enabled}>{service.name}{!service.enabled ? '（已停用）' : !service.ready ? '（未配置完整）' : ''}</option>)}
        </select></label>
        <label>文本模型<select aria-label="文本模型" value={selectedModel} onChange={e => patch({ textModel: e.target.value })}>
          {!selectedService?.models.includes(selectedModel) && <option value={selectedModel}>{selectedModel ? `${selectedModel}（已失效）` : '请先在设置中添加模型'}</option>}
          {selectedService?.models.map(model => <option key={model} value={model}>{model}</option>)}
        </select></label>
        {(!selectedService?.enabled || !selectedService?.models.includes(selectedModel)) && <small className="choice-error">当前服务或模型不可用，请重新选择或修改设置。</small>}
        {selectedService && !selectedService.ready && <small>请在工作台设置中补全此服务的地址、模型和密钥。</small>}
      </fieldset>}
      {!isReference && !isSelection && !isConcat && !isExtraction && kind !== 'story.prompt' && !isText && <label>生成服务<select aria-label="生成服务" value={config.provider || 'runninghub'} onChange={e => patch({ provider: e.target.value as 'runninghub' | 'comfyui' })}><option value="runninghub">RunningHub 云端</option><option value="comfyui">本地 ComfyUI</option></select><small>{config.provider === 'comfyui' ? '使用设置中的本地工作流；无需开启云端生成。' : '提示词和引用素材将上传至云端服务。'}</small></label>}
      {!isReference && !isSelection && !isConcat && !isExtraction && !isText && kind !== 'story.prompt' && config.provider !== 'comfyui' && <label>生成工作流<select aria-label="生成工作流" value={config.workflowId || (isVideoGeneration ? selectedWorkflow?.id : '') || ''} onChange={e => patch({ workflowId: e.target.value })}>
        <option value="">{isVideoGeneration ? '使用默认视频工作流' : '默认工作流（兼容原配置）'}</option>
        {config.workflowId && !selectedWorkflow && <option value={config.workflowId}>原工作流已失效，请重新选择</option>}
        {availableWorkflows.map(workflow => <option key={workflow.id} value={workflow.id} disabled={!workflow.enabled}>{workflow.name}{workflow.enabled ? '' : '（已停用）'}</option>)}
      </select>{config.workflowId && !selectedWorkflow?.enabled ? <small className="choice-error">所选工作流已停用或不适用于当前节点。</small> : <small>在工作台设置 → 云端工作流中添加或编辑。</small>}</label>}
      {videoWorkflowMissing && <small className="choice-error">请在设置中添加视频工作流，并在此选择后生成。</small>}
      {isVideoGeneration && config.provider !== 'comfyui' && selectedWorkflow?.builtin === 'minimax_h3' && <><small>MiniMax H3 全能参考（动作迁移）：最多 9 张图片、3 段参考视频、3 段音频、3 段视频音频，至少连接或选择一个参考素材。工作流按实际输入自动匹配。参考视频使用画面；“参考音频”用于独立录音；“视频音频”直接传入工作流的配套音轨输入，没有参考视频也会上传，不做配对拦截；原生节点可能不采用无配对音轨。配套音轨先占用 Audio 编号，独立音频随后编号。声音来自视频时，可先使用“提取视频音频”节点。音色参考不等于复述录音，请明确角色及逐字台词；不会自动替换成原音轨。</small><MiniMaxSettings key={node.id} config={config} patch={patch} disabled={busy || !!runStage}/></>}
      {kind === 'video.combat' && config.provider !== 'comfyui' && selectedWorkflow?.builtin === 'minimax_h3_combat' && <><small>生成视频-武打使用 H3 文武05 工作流：连接1–9张参考图，可选1–3段音频和1–3段视频。未使用的示例输入会自动移除；音频传入 ref_audios，视频传入 ref_videos。默认24fps，声音由工作流生成。</small><CombatVideoSettings key={node.id} config={config} patch={patch} disabled={busy || !!runStage}/></>}
      {isVideoGeneration && <><VideoDuration key={node.id} seconds={config.seconds ?? (kind === 'video.combat' ? 8 : undefined)} onChange={seconds => patch({ seconds, durationSource: 'manual' })}/>
        <label className="check-row"><input type="checkbox" aria-label="跟随上游时长" checked={config.durationSource === 'upstream' || config.seconds === undefined} onChange={event => patch(event.target.checked ? { durationSource: 'upstream', seconds: undefined } : { durationSource: 'manual', seconds: config.seconds ?? 5 })}/>跟随上游时长</label>
        <small>手动填写优先，范围 1–30 秒；跟随上游时采用分镜或扩写时长，无上游时默认 5 秒。改变时长后建议同步调整扩写节奏。实际输出按工作流帧数取整，自定义工作流需映射时长参数。</small></>}
      {kind === 'prompt.video_expand' && <><label>目标时长（秒）<input aria-label="扩写目标时长（秒）" type="number" min={4} max={15} step={0.1} disabled={!!durationSource} value={durationSource ? inheritedSeconds || '' : config.seconds ?? 5}
        onChange={event => patch({ seconds: event.target.value === '' ? undefined : Number(event.target.value) })}
        onBlur={() => patch({ seconds: Math.min(15, Math.max(4, config.seconds || 5)) })}/></label>
        {durationSource && <small className="duration-source">时长来自「{durationSource.data.title}」，请在上游调整{inheritedSeconds ? `（${inheritedSeconds} 秒）` : '或先选择分镜'}。</small>}
        <small>支持最多9张图片和3段参考视频，仅根据文字和画面扩写。参考音频请直接连接视频生成节点，扩写不发送录音，参考视频也会去掉声音；旧音频连线和勾选将被忽略。需要准确对白时，请在文字中写明角色和逐字台词；音色用途可写“Audio 1 参考某角色音色”。同类素材按端口编号传入，再追加勾选素材。视频最多20 MiB、120秒；输出六段英文，对白保留原语言。</small></>}
      {isReference && <label>锁定素材版本<select value={config.assetId || ''} onChange={e => patch({ assetId: e.target.value })}><option value="">选择素材…</option>{s.assets.filter(a => a.mime.startsWith(kind === 'asset.audio' ? 'audio/' : kind === 'asset.video' ? 'video/' : 'image/')).map(a => <option key={a.id} value={a.id}>{a.name} · {a.sha256.slice(0, 6)}</option>)}</select></label>}
      {!isReference && !isTrim && (kind.includes('image') || kind.startsWith('video') || kind === 'audio.tts' || kind === 'prompt.video_expand') && <fieldset><legend>锁定参考素材</legend><small>勾选图片会自动创建或复用素材节点并连线；取消勾选移除对应线。音视频仍按勾选顺序传入。</small><div className="reference-list">{s.assets.filter(a => kind === 'prompt.video_expand' ? /^(image|video)\//.test(a.mime) : isVideoGeneration ? /^(image|video|audio)\//.test(a.mime) : a.mime.startsWith(kind === 'audio.tts' ? 'audio/' : kind === 'video.sound_effects' ? 'video/' : 'image/')).map(a => <label className="check-row" key={a.id}><input type="checkbox" disabled={busy || !!runStage} checked={!!config.referenceIds?.includes(a.id) || (a.mime.startsWith('image/') && wiredImageIds.has(a.id))} onChange={e => {
          try {
            if (a.mime.startsWith('image/')) s.selectReferenceImage(node.id, a.id, e.target.checked);
            else patch({ referenceIds: e.target.checked ? [...(config.referenceIds || []), a.id] : config.referenceIds?.filter(id => id !== a.id) });
            setReferenceNotice(undefined);
          } catch (error) { setReferenceNotice({ id: node.id, text: error instanceof Error ? error.message : String(error) }); }
        }}/><span>{a.name}<small>{a.sha256.slice(0, 8)}</small></span></label>)}{!s.assets.length && <p className="muted">从左侧导入参考素材</p>}</div></fieldset>}
      {hasReferenceAudio && <><label>演绎风格<input value={config.voiceStyle || ''} onChange={e => patch({ voiceStyle: e.target.value })}/></label><label className="check-row"><input type="checkbox" checked={config.voiceAuthorized || false} onChange={e => patch({ voiceAuthorized: e.target.checked })}/>我已获得参考声音的使用授权</label></>}
      {task && <div className={'task-summary ' + (task.error ? 'error-box' : '')}><span>{task.error ? <AlertCircle size={14}/> : <span className={'status-dot ' + task.status}/>} {STATUS[task.status]}{task.reused ? ' · 缓存复用' : ''}</span>{task.error && <p>{task.error}</p>}{task.external_id && <small>云端任务：{task.external_id}</small>}</div>}
      {kind === 'story.prompt' && <p className="muted">这是故事输入节点，只输出你填写的文字，不调用大模型。生成新文本请连接“剧本扩写”节点，选择文本服务和模型，并勾选左侧底部的“仅本地编辑”开关，切换为“允许云端生成”。</p>}
      {kind === 'image.character' && <p className="muted">支持最多 8 个参考图连接点，连接后自动显示下一个。按编号顺序传入，勾选的额外素材追加在后；默认 Image2 连线与勾选合计最多 8 张。输出三视图与右侧细节设定图。</p>}
      {!isReference && !isSelection && !isConcat && !isExtraction && kind !== 'story.prompt' && <div><button type="button" aria-pressed={config.overwriteCache === true} disabled={busy || !!runStage} onClick={() => patch({ overwriteCache: config.overwriteCache !== true })}>{config.overwriteCache === true && <Check size={14}/>}覆盖缓存：{config.overwriteCache === true ? '开启' : '关闭'}</button><small style={{ display: 'block', marginTop: 8 }}>{config.overwriteCache === true ? '运行时重新调用生成服务并更新缓存，可能产生费用；历史素材保留。' : '运行时优先复用相同输入的缓存；开启后强制重新生成。'}</small></div>}
      {!isFrame && <div className="field-row"><button className="primary" disabled={busy || !!runStage || videoWorkflowMissing || selectionInvalid || trimInvalid} onClick={() => run([node.id])}><Play size={14}/>{runStage || (kind === 'story.prompt' ? '输出故事内容' : isSelection ? '输出所选分镜' : isConcat ? '拼接文本' : isTrim ? '裁剪' + trimMedia : isExtraction ? '提取音频' : '运行节点')}</button><button disabled={busy || !!runStage || videoWorkflowMissing || selectionInvalid || trimInvalid} onClick={() => run([node.id], true)}>{kind === 'story.prompt' ? '重新输出内容' : isSelection ? '重新输出分镜' : isConcat ? '重新拼接' : isTrim ? '重新裁剪' : isExtraction ? '重新提取' : '重新生成'}</button></div>}
      {kind === 'shots.extract' && <small>每条分镜为 4–15 秒。连接“分镜选择”挑选单条，再连接“视频提示词扩写”完善画面与声音描述。</small>}
      {kind === 'character.extract' && <small>连接故事或剧本后运行，审核角色设定，再确认加入角色库并创建各自的形象节点。</small>}
      {kind === 'location.extract' && <small>连接故事或剧本，提取可复用的场景环境，确认后加入场景库并创建四视图节点。</small>}
      {kind === 'image.location' && <small>生成一张场景四视图：2×2 排列前、右、后、左四个方向，保持同一空间布局与光照。采用后同步关联场景参考图；自定义工作流建议使用方形画布。</small>}
      {kind === 'image.prop' && <small>生成一张道具四视图：2×2 排列前、右、后、左四个方向，保持同一道具的结构、材质与配件一致。可填写描述、连接上游文本，也可只提供参考图。最多 8 个图片连接点，连上后自动显示下一个；默认 Image2 连线与勾选合计最多 8 张。自定义工作流建议使用方形画布。</small>}
      {kind === 'video.image_to_video' && <small>支持最多 9 张图片、3 段参考视频、3 段音频和 3 段视频音频。连接后自动出现下一同类连接点；同类素材按端口编号排序，再追加勾选素材。这里勾选的视频作为画面参考；“视频音频”端口无参考视频时也会直传；是否采用取决于云端工作流。普通音频参考连接“参考音频”端口。</small>}
      {!!task?.output.locations?.length && <section className="result-section"><h3>场景草案 · {task.output.locations.length} 处</h3>{task.output.locations.map((location, index) => <details key={index}><summary>{location.name}</summary><p>{location.description}</p><p>布局：{location.layout || '未指定'}</p><p>限制：{location.restrictions || '无'}</p></details>)}<button disabled={busy} onClick={() => importLocations(task.output.locations!, task.id, false, { visualStyle: config.visualStyle })}>确认场景并创建四视图节点</button></section>}
      {kind === 'image.character' && <small>生成同一张横向设定图：左侧为正面、侧面、背面三视图，右侧为 3–4 个面部、发型、服装材质及已有配饰细节特写。所有视图保持同一角色、同一造型。已采用的旧图片需点击“重新生成”更新；采用后同步关联角色库参考图。自定义工作流建议使用横向画布。</small>}
      {!!task?.output.characters?.length && <section className="result-section"><h3>角色草案 · {task.output.characters.length} 人</h3>{task.output.characters.map((character, index) => <details key={index}><summary>{character.name}</summary><p>{character.description}</p><p>外貌：{character.appearance || '未指定'}</p><p>服装：{character.wardrobe || '未指定'}</p><p>限制：{character.restrictions || '无'}</p></details>)}<button disabled={busy} onClick={() => importCharacters(task.output.characters!, task.id, false, { visualStyle: config.visualStyle })}>确认角色并创建形象节点</button></section>}
      {textResult && task && <>{(isText || isConcat) && task.status === 'completed' ? <TextResultEditor key={`${node.id}:${task.id}`} nodeId={node.id} taskId={task.id} output={{ ...task.output, text: textResult }} busy={busy}/> : <section className="result-section"><h3>文本结果</h3><pre>{textResult}</pre></section>}{task.output.shots && <button onClick={() => importShots(task.output.shots!)}>确认分镜并加入画布</button>}</>}
      {current?.mime.startsWith('video/') && <section className="result-section"><h3>当前视频</h3><video key={current.id} src={mediaUrl(current.id)} controls preload="metadata"
        onLoadedMetadata={event => { const seconds = Math.floor(event.currentTarget.duration * 1000) / 1000; setVideoMetadata(Number.isFinite(seconds) && seconds > 0 ? { id: current.id, seconds } : undefined); }}
        onError={() => setVideoMetadata(undefined)}/>
        <small>{videoSeconds ? `素材实际时长 ${videoSeconds} 秒；加入后可在时间线裁切。` : '正在读取素材时长；无法加载时请检查原视频文件。'}</small>
        <button disabled={!videoSeconds} onClick={() => { if (videoSeconds) addClip(current, node.data.title, videoSeconds); }}><Film size={14}/>批准并加入时间线</button></section>}
      {candidates.length > 0 && <section className="result-section"><h3>候选版本 <span>{candidates.length}</span></h3><small>采用版本将锁定素材；重新生成仍保留旧候选。</small><div className="candidates">{candidates.map(a => <div key={a.id} className={config.assetId === a.id ? 'candidate adopted' : 'candidate'}>{a.mime.startsWith('image/') ? <img src={thumbnailUrl(a.id)} alt={a.name} loading="lazy"/> : a.mime.startsWith('video/') ? <video src={mediaUrl(a.id)} controls preload="metadata"/> : <audio src={mediaUrl(a.id)} controls preload="metadata"/>}<div><small>{new Date(a.createdAt * 1000).toLocaleTimeString()} · {a.sha256.slice(0, 6)}</small><button onClick={() => { patch({ assetId: a.id }); if (kind === 'image.character' && typeof config.characterId === 'string') adoptCharacterImage(config.characterId, a.id); if (kind === 'image.location' && typeof config.locationId === 'string') adoptLocationImage(config.locationId, a.id); }}><Check size={12}/>{config.assetId === a.id ? '已采用' : '采用'}</button></div></div>)}</div></section>}
      {candidates.length > 1 && <section className="result-section"><h3>版本对比</h3><div className="field-row">{[0, 1].map(index => <label key={index}>版本 {index + 1}<select aria-label={`对比版本${index + 1}`} value={compare[index] || candidates[index]?.id} onChange={e => setCompare(current => { const next = [...current]; next[index] = e.target.value; return next; })}>{candidates.map(asset => <option key={asset.id} value={asset.id}>{asset.sha256.slice(0, 8)} · {new Date(asset.createdAt * 1000).toLocaleTimeString()}</option>)}</select></label>)}</div><div className="candidate-compare">{[0, 1].map(index => { const asset = candidates.find(a => a.id === compare[index]) || candidates[index]; return asset ? <figure key={index}>{asset.mime.startsWith('image/') ? <img src={mediaUrl(asset.id)} alt={`对比版本${index + 1}`}/> : asset.mime.startsWith('video/') ? <video src={mediaUrl(asset.id)} controls preload="metadata"/> : <audio src={mediaUrl(asset.id)} controls/>}<figcaption>{asset.sha256.slice(0, 8)}<button onClick={() => { patch({ assetId: asset.id }); if (kind === 'image.character' && typeof config.characterId === 'string') adoptCharacterImage(config.characterId, asset.id); if (kind === 'image.location' && typeof config.locationId === 'string') adoptLocationImage(config.locationId, asset.id); }}>采用此版本</button></figcaption></figure> : null; })}</div></section>}
    </div>
  </aside>;
}
