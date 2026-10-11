import { Settings2, Play, Check, Film, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { BatchGeneration } from './BatchGeneration';
import { VideoDuration } from './VideoDuration';
import { ShotSelection } from './ShotSelection';
import { useStudio } from './store';
import { mediaUrl, thumbnailUrl } from './api';
import { STATUS, type Asset, type Config, type GenerationOptions, type Shot, type CharacterDraft, type LocationDraft, type PeopleDoc } from './types';

export function Inspector({ people, run, addClip, importShots, importCharacters, adoptCharacterImage, importLocations, adoptLocationImage, generationOptions, runStage }: { people: PeopleDoc; run: (ids: string[], force?: boolean) => void; addClip: (asset: Asset, title: string, seconds: number) => void; importShots: (shots: Shot[]) => void; importCharacters: (characters: CharacterDraft[], taskId: string, generate?: boolean, generationConfig?: Config) => void; adoptCharacterImage: (characterId: string, assetId: string) => void; importLocations: (locations: LocationDraft[], taskId: string, generate?: boolean, generationConfig?: Config) => void; adoptLocationImage: (locationId: string, assetId: string) => void; generationOptions: GenerationOptions; runStage: string }) {
  const [compare, setCompare] = useState<string[]>([]);
  const s = useStudio();
  const node = s.nodes.find(n => n.selected);
  if (!node) return <aside className="inspector"><div className="panel-title"><Settings2 size={15}/>镜头属性</div><div className="inspector-empty"><Settings2 size={30} strokeWidth={1}/><h3>选择一个节点</h3><p>编辑内容、绑定参考素材，<br/>查看生成记录与候选版本。</p></div><div className="workflow-guide"><span className="eyebrow">创作路径</span><p>故事文本 → 分镜图 → 视频</p><p>配音与字幕 → 时间线 → 成片</p><small>连线定义生成依赖，时间线定义镜头顺序。</small></div></aside>;
  const config = node.data.config;
  const kind = node.data.kind;
  const task = s.tasks.find(t => t.node_id === node.id);
  const candidates = s.assets.filter(a => a.nodeId === node.id);
  const current = s.assets.find(a => a.id === (config.assetId || task?.output.assets?.[0]));
  const patch = (value: Partial<Config>) => s.patch(node.id, { config: { ...config, ...value } });
  const isReference = kind.endsWith('.reference') || kind.startsWith('asset.');
  const textResult = task?.output.text;
  const busy = !!task && ['queued', 'running', 'cancel_requested'].includes(task.status);
  const isSelection = kind === 'shots.select';
  const isText = ['script.expand', 'shots.extract', 'character.extract', 'location.extract', 'prompt.video_expand'].includes(kind);
  const availableWorkflows = generationOptions.workflows.filter(w => w.kinds.includes(kind));
  const selectedWorkflow = availableWorkflows.find(w => w.id === (config.workflowId || (kind === 'video.image_to_video' ? 'builtin-minimax-h3' : '')));
  const videoWorkflowMissing = kind === 'video.image_to_video' && config.provider !== 'comfyui' && !selectedWorkflow?.enabled;
  const serviceId = config.textServiceId || 'legacy';
  const selectedService = generationOptions.textServices.find(s => s.id === serviceId);
  const selectedModel = serviceId === 'legacy' ? selectedService?.defaultModel || '' : config.textModel || selectedService?.defaultModel || '';
  const upstreamIds = s.edges.filter(edge => edge.target === node.id && edge.targetHandle === 'text' && edge.data?.kind !== 'sequence').map(edge => edge.source);
  const upstreamTask = s.tasks.filter(t => upstreamIds.includes(t.node_id)).sort((a, b) => b.created_at - a.created_at)[0];
  const selectionInvalid = isSelection && (upstreamTask?.status !== 'completed'
    || s.nodes.some(item => upstreamIds.includes(item.id) && item.data.status === 'dirty')
    || config.shotIndex === undefined || !config.selectedShot
    || JSON.stringify(upstreamTask?.output.shots?.[config.shotIndex]) !== JSON.stringify(config.selectedShot));
  const characterSource = kind === 'character.extract' ? task : kind === 'image.character' ? upstreamTask : undefined;
  const locationSource = kind === 'location.extract' ? task : kind === 'image.location' ? upstreamTask : undefined;
  return <aside className="inspector" key={node.id}>
    <div className="panel-title"><Settings2 size={15}/>节点属性<span className="muted">{s.definitions[kind]?.displayName}</span></div>
    <div className="inspector-scroll">
      <label>名称<input value={node.data.title} onChange={e => s.patch(node.id, { title: e.target.value })}/></label>
      {characterSource?.status === 'completed' && !!characterSource.output.characters?.length && <BatchGeneration key={`${node.id}:${characterSource.id}`} kind="image.character" count={characterSource.output.characters.length} taskId={characterSource.id} profiles={people.characters} initialConfig={kind === 'image.character' ? config : {}} options={generationOptions} busy={busy} runStage={runStage} generate={selection => importCharacters(characterSource.output.characters!, characterSource.id, true, selection)}/>}
      {locationSource?.status === 'completed' && !!locationSource.output.locations?.length && <BatchGeneration key={`${node.id}:${locationSource.id}`} kind="image.location" count={locationSource.output.locations.length} taskId={locationSource.id} profiles={people.locations} initialConfig={kind === 'image.location' ? config : {}} options={generationOptions} busy={busy} runStage={runStage} generate={selection => importLocations(locationSource.output.locations!, locationSource.id, true, selection)}/>}
      {isSelection && <><ShotSelection nodeId={node.id}/><small>本地选择，不调用大模型；输出所选分镜的画面、对白、镜头和时长。</small></>}
      {!isReference && !isSelection && <label>{kind === 'audio.tts' ? '对白 / 声音描述' : kind === 'story.prompt' ? '故事内容' : kind === 'prompt.video_expand' ? '补充要求 / 参考说明' : '提示词'}<textarea rows={8} value={config.prompt || ''} placeholder={kind === 'prompt.video_expand' ? '连接所选分镜，可补充参考图片角色、场景、风格和保留要求…' : '描述角色、场景、动作与镜头语言…'} onChange={e => patch({ prompt: e.target.value })}/></label>}
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
      {!isReference && !isSelection && kind !== 'story.prompt' && !isText && <label>生成服务<select aria-label="生成服务" value={config.provider || 'runninghub'} onChange={e => patch({ provider: e.target.value as 'runninghub' | 'comfyui' })}><option value="runninghub">RunningHub 云端</option><option value="comfyui">本地 ComfyUI</option></select><small>{config.provider === 'comfyui' ? '使用设置中的本地工作流；无需开启云端生成。' : '提示词和引用素材将上传至云端服务。'}</small></label>}
      {!isReference && !isSelection && !isText && kind !== 'story.prompt' && config.provider !== 'comfyui' && <label>生成工作流<select aria-label="生成工作流" value={config.workflowId || (kind === 'video.image_to_video' ? selectedWorkflow?.id : '') || ''} onChange={e => patch({ workflowId: e.target.value })}>
        <option value="">{kind === 'video.image_to_video' ? '使用默认视频工作流' : '默认工作流（兼容原配置）'}</option>
        {config.workflowId && !selectedWorkflow && <option value={config.workflowId}>原工作流已失效，请重新选择</option>}
        {availableWorkflows.map(workflow => <option key={workflow.id} value={workflow.id} disabled={!workflow.enabled}>{workflow.name}{workflow.enabled ? '' : '（已停用）'}</option>)}
      </select>{config.workflowId && !selectedWorkflow?.enabled ? <small className="choice-error">所选工作流已停用或不适用于当前节点。</small> : <small>在工作台设置 → 云端工作流中添加或编辑。</small>}</label>}
      {videoWorkflowMissing && <small className="choice-error">请在设置中添加视频工作流，并在此选择后生成。</small>}
      {kind === 'video.image_to_video' && config.provider !== 'comfyui' && selectedWorkflow?.builtin === 'minimax_h3' && <small>默认按素材数量匹配 workflow_json_new.py：1–9 张图片，可搭配 1 段音频或 1 段视频。视频模板使用视频音轨；更多音视频参考请选择其它工作流。</small>}
      {kind === 'video.image_to_video' && <><VideoDuration key={node.id} seconds={config.seconds} onChange={seconds => patch({ seconds })}/><small>可输入 1–30 秒，默认 5 秒。实际输出按工作流帧数规则取整；自定义工作流需映射时长参数。</small></>}
      {kind === 'prompt.video_expand' && <><label>目标时长（秒）<input aria-label="扩写目标时长（秒）" type="number" min={4} max={15} step={0.1} value={config.seconds ?? 5}
        onChange={event => patch({ seconds: event.target.value === '' ? undefined : Number(event.target.value) })}
        onBlur={() => patch({ seconds: Math.min(15, Math.max(4, config.seconds || 5)) })}/></label>
        <small>参考规范输出六段英文，对白保留原语言。连接“分镜选择”时使用上游时长；纯文字可直接填写要求。参考图片须使用支持图片输入的文本模型，并与视频节点保持相同素材顺序。</small></>}
      {isReference && <label>锁定素材版本<select value={config.assetId || ''} onChange={e => patch({ assetId: e.target.value })}><option value="">选择素材…</option>{s.assets.filter(a => a.mime.startsWith(kind === 'asset.audio' ? 'audio/' : kind === 'asset.video' ? 'video/' : 'image/')).map(a => <option key={a.id} value={a.id}>{a.name} · {a.sha256.slice(0, 6)}</option>)}</select></label>}
      {!isReference && (kind.includes('image') || kind.startsWith('video') || kind === 'audio.tts' || kind === 'prompt.video_expand') && <fieldset><legend>锁定参考素材</legend><small>按勾选顺序传入；角色与场景也可通过画布连线引用。</small><div className="reference-list">{s.assets.filter(a => kind === 'video.image_to_video' ? /^(image|video|audio)\//.test(a.mime) : a.mime.startsWith(kind === 'audio.tts' ? 'audio/' : kind === 'video.sound_effects' ? 'video/' : 'image/')).map(a => <label className="check-row" key={a.id}><input type="checkbox" checked={config.referenceIds?.includes(a.id) || false} onChange={e => patch({ referenceIds: e.target.checked ? [...(config.referenceIds || []), a.id] : config.referenceIds?.filter(id => id !== a.id) })}/><span>{a.name}<small>{a.sha256.slice(0, 8)}</small></span></label>)}{!s.assets.length && <p className="muted">从左侧导入参考素材</p>}</div></fieldset>}
      {kind === 'audio.tts' && !!config.referenceIds?.length && <><label>演绎风格<input value={config.voiceStyle || ''} onChange={e => patch({ voiceStyle: e.target.value })}/></label><label className="check-row"><input type="checkbox" checked={config.voiceAuthorized || false} onChange={e => patch({ voiceAuthorized: e.target.checked })}/>我已获得参考声音的使用授权</label></>}
      {task && <div className={'task-summary ' + (task.error ? 'error-box' : '')}><span>{task.error ? <AlertCircle size={14}/> : <span className={'status-dot ' + task.status}/>} {STATUS[task.status]}{task.reused ? ' · 缓存复用' : ''}</span>{task.error && <p>{task.error}</p>}{task.external_id && <small>云端任务：{task.external_id}</small>}</div>}
      {kind === 'story.prompt' && <p className="muted">这是故事输入节点，只输出你填写的文字，不调用大模型。生成新文本请连接“剧本扩写”节点，选择文本服务和模型，并勾选左侧底部的“仅本地编辑”开关，切换为“允许云端生成”。</p>}
      {!isReference && !isSelection && kind !== 'story.prompt' && <div><button type="button" aria-pressed={config.overwriteCache === true} disabled={busy || !!runStage} onClick={() => patch({ overwriteCache: config.overwriteCache !== true })}>{config.overwriteCache === true && <Check size={14}/>}覆盖缓存：{config.overwriteCache === true ? '开启' : '关闭'}</button><small style={{ display: 'block', marginTop: 8 }}>{config.overwriteCache === true ? '运行时重新调用生成服务并更新缓存，可能产生费用；历史素材保留。' : '运行时优先复用相同输入的缓存；开启后强制重新生成。'}</small></div>}
      <div className="field-row"><button className="primary" disabled={busy || !!runStage || videoWorkflowMissing || selectionInvalid} onClick={() => run([node.id])}><Play size={14}/>{runStage || (kind === 'story.prompt' ? '输出故事内容' : isSelection ? '输出所选分镜' : '运行节点')}</button><button disabled={busy || !!runStage || videoWorkflowMissing || selectionInvalid} onClick={() => run([node.id], true)}>{kind === 'story.prompt' ? '重新输出内容' : isSelection ? '重新输出分镜' : '重新生成'}</button></div>
      {kind === 'shots.extract' && <small>每条分镜为 4–15 秒。连接“分镜选择”挑选单条，再连接“视频提示词扩写”完善画面与声音描述。</small>}
      {kind === 'character.extract' && <small>连接故事或剧本后运行，审核角色设定，再确认加入角色库并创建各自的形象节点。</small>}
      {kind === 'location.extract' && <small>连接故事或剧本，提取可复用的场景环境，确认后加入场景库并创建四视图节点。</small>}
      {kind === 'image.location' && <small>生成一张场景四视图：2×2 排列前、右、后、左四个方向，保持同一空间布局与光照。采用后同步关联场景参考图；自定义工作流建议使用方形画布。</small>}
      {kind === 'video.image_to_video' && <small>支持最多 9 张图片、3 段音频、3 段视频。连接后自动出现下一参考连接点；同类素材按端口编号排序，再追加勾选的素材，请配置相应工作流输入映射。</small>}
      {!!task?.output.locations?.length && <section className="result-section"><h3>场景草案 · {task.output.locations.length} 处</h3>{task.output.locations.map((location, index) => <details key={index}><summary>{location.name}</summary><p>{location.description}</p><p>布局：{location.layout || '未指定'}</p><p>限制：{location.restrictions || '无'}</p></details>)}<button disabled={busy} onClick={() => importLocations(task.output.locations!, task.id)}>确认场景并创建四视图节点</button></section>}
      {kind === 'image.character' && <small>生成一张角色三视图：正面、侧面、背面，全身等比例、外貌与服装一致。旧图片需点击“重新生成”更新；采用后同步关联角色库参考图。自定义工作流建议使用横向画布。</small>}
      {!!task?.output.characters?.length && <section className="result-section"><h3>角色草案 · {task.output.characters.length} 人</h3>{task.output.characters.map((character, index) => <details key={index}><summary>{character.name}</summary><p>{character.description}</p><p>外貌：{character.appearance || '未指定'}</p><p>服装：{character.wardrobe || '未指定'}</p><p>限制：{character.restrictions || '无'}</p></details>)}<button disabled={busy} onClick={() => importCharacters(task.output.characters!, task.id)}>确认角色并创建形象节点</button></section>}
      {textResult && <section className="result-section"><h3>文本结果</h3><pre>{textResult}</pre>{task?.output.shots && <button onClick={() => importShots(task.output.shots!)}>确认分镜并加入画布</button>}</section>}
      {current?.mime.startsWith('video/') && <section className="result-section"><h3>当前视频</h3><video src={mediaUrl(current.id)} controls preload="metadata"/><button onClick={() => addClip(current, node.data.title, config.seconds || 5)}><Film size={14}/>批准并加入时间线</button></section>}
      {candidates.length > 0 && <section className="result-section"><h3>候选版本 <span>{candidates.length}</span></h3><small>采用版本将锁定素材；重新生成仍保留旧候选。</small><div className="candidates">{candidates.map(a => <div key={a.id} className={config.assetId === a.id ? 'candidate adopted' : 'candidate'}>{a.mime.startsWith('image/') ? <img src={thumbnailUrl(a.id)} alt={a.name} loading="lazy"/> : a.mime.startsWith('video/') ? <video src={mediaUrl(a.id)} controls preload="metadata"/> : <audio src={mediaUrl(a.id)} controls preload="metadata"/>}<div><small>{new Date(a.createdAt * 1000).toLocaleTimeString()} · {a.sha256.slice(0, 6)}</small><button onClick={() => { patch({ assetId: a.id }); if (kind === 'image.character' && typeof config.characterId === 'string') adoptCharacterImage(config.characterId, a.id); if (kind === 'image.location' && typeof config.locationId === 'string') adoptLocationImage(config.locationId, a.id); }}><Check size={12}/>{config.assetId === a.id ? '已采用' : '采用'}</button></div></div>)}</div></section>}
      {candidates.length > 1 && <section className="result-section"><h3>版本对比</h3><div className="field-row">{[0, 1].map(index => <label key={index}>版本 {index + 1}<select aria-label={`对比版本${index + 1}`} value={compare[index] || candidates[index]?.id} onChange={e => setCompare(current => { const next = [...current]; next[index] = e.target.value; return next; })}>{candidates.map(asset => <option key={asset.id} value={asset.id}>{asset.sha256.slice(0, 8)} · {new Date(asset.createdAt * 1000).toLocaleTimeString()}</option>)}</select></label>)}</div><div className="candidate-compare">{[0, 1].map(index => { const asset = candidates.find(a => a.id === compare[index]) || candidates[index]; return asset ? <figure key={index}>{asset.mime.startsWith('image/') ? <img src={mediaUrl(asset.id)} alt={`对比版本${index + 1}`}/> : asset.mime.startsWith('video/') ? <video src={mediaUrl(asset.id)} controls preload="metadata"/> : <audio src={mediaUrl(asset.id)} controls/>}<figcaption>{asset.sha256.slice(0, 8)}<button onClick={() => { patch({ assetId: asset.id }); if (kind === 'image.character' && typeof config.characterId === 'string') adoptCharacterImage(config.characterId, asset.id); if (kind === 'image.location' && typeof config.locationId === 'string') adoptLocationImage(config.locationId, asset.id); }}>采用此版本</button></figcaption></figure> : null; })}</div></section>}
    </div>
  </aside>;
}
