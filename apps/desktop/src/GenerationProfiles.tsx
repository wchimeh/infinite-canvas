import { useState } from 'react';
import { Plus, Copy, Trash2, Upload } from 'lucide-react';
import { api, json } from './api';
import type { AppSettings, CloudWorkflow, TextService, WorkflowMapping } from './types';

const KIND_NAMES: Record<string, string> = { 'image.location': '生成场景图', 'image.character': '生成角色图', 'image.generate': '生成图片', 'image.variation': '图片变体', 'video.image_to_video': '生成视频' };
const SOURCES: Record<WorkflowMapping['source'], string> = { prompt: '提示词', image: '参考图片', video: '参考视频', audio: '参考音频', seconds: '时长（秒）', fps: '帧率', seed: '随机种子' };
type Props = { mode: 'text' | 'workflows'; config: AppSettings; patch: (value: Partial<AppSettings>) => void; builtins: CloudWorkflow[]; save: () => Promise<void>; saved: () => void };

export function GenerationProfiles({ mode, config, patch, builtins, save, saved }: Props) {
  const [selected, setSelected] = useState('');
  const [graphDrafts, setGraphDrafts] = useState<Record<string, NonNullable<CloudWorkflow['workflow']>>>({});
  const [secret, setSecret] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  const services = config.textServices;
  const workflows = [...builtins, ...config.cloudWorkflows].filter(workflow => workflow.kinds.some(kind => kind in KIND_NAMES));
  const service = services.find(s => s.id === selected);
  const workflow = workflows.find(w => w.id === selected);
  const readonly = !!workflow?.id.startsWith('builtin-');
  function choose(id: string) { setSelected(id); setSecret(''); setError(''); setMessage(''); }
  function updateService(value: Partial<TextService>) { if (service) patch({ textServices: services.map(s => s.id === selected ? { ...s, ...value } : s) }); }
  function updateWorkflow(value: Partial<CloudWorkflow>) { if (workflow && !readonly) { setError(''); setMessage(''); patch({ cloudWorkflows: config.cloudWorkflows.map(w => w.id === selected ? { ...w, ...value } : w) }); } }
  function switchSubmission(full: boolean) {
    if (!workflow) return;
    if (workflow.workflow !== undefined) setGraphDrafts(drafts => ({ ...drafts, [workflow.id]: workflow.workflow! }));
    updateWorkflow({ workflow: full ? graphDrafts[workflow.id] ?? '{}' : undefined });
  }
  async function checkWorkflow() {
    if (!workflow) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await api<CloudWorkflow>('/settings/workflows/validate', json('POST', workflow));
      setMessage('当前工作流配置检查通过；尚未保存，未调用云端生成');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  function addService() {
    const next: TextService = { id: crypto.randomUUID(), name: '新文本服务', baseUrl: '', models: [''], defaultModel: '', enabled: true };
    patch({ textServices: [...services, next] }); choose(next.id);
  }
  function addWorkflow(source?: CloudWorkflow) {
    const next: CloudWorkflow = source ? { ...structuredClone(source), id: crypto.randomUUID(), name: source.name + ' · 副本' } : {
      id: crypto.randomUUID(), name: '新图片工作流', kinds: ['image.generate'], version: 1, enabled: true,
      workflow: '{}', workflowId: '', nodeInfoList: [], mappings: [{ source: 'prompt', nodeId: '', fieldName: 'text' }], resultNodes: [''],
    };
    patch({ cloudWorkflows: [...config.cloudWorkflows, next] }); choose(next.id);
  }
  async function credential(remove = false) {
    if (!service) return;
    setBusy(true); setError(''); setMessage('');
    try {
      if (!remove) await save();
      const result = await api<AppSettings>(`/settings/credentials/text-${service.id}`, remove ? { method: 'DELETE' } : json('PUT', { key: secret }));
      patch({ credentials: result.credentials }); setSecret(''); saved(); setMessage(remove ? '该服务的密钥已撤销' : '该服务的密钥已保存在系统中');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  async function importWorkflow(file: File) {
    setError(''); setMessage(''); setBusy(true);
    try {
      if (file.size > 1024 * 1024) throw new Error('工作流配置不能超过 1 MB');
      const data = JSON.parse(await file.text()) as CloudWorkflow;
      if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('请导入工作流配置对象');
      if (!('kinds' in data) && Object.values(data).length && Object.values(data).every(node => node && typeof node === 'object' && 'class_type' in node && 'inputs' in node)) {
        addWorkflow({ id: crypto.randomUUID(), name: file.name.replace(/\.json$/i, ''), kinds: ['image.generate'], enabled: true, version: 1,
          workflow: data as unknown as NonNullable<CloudWorkflow['workflow']>, mappings: [], nodeInfoList: [], resultNodes: [''] });
        setMessage('已导入完整工作流草稿，请选择适用节点，填写输出节点和输入映射后保存设置');
        return;
      }
      const draft = { ...data, id: crypto.randomUUID(), name: typeof data.name === 'string' ? data.name : '导入工作流', enabled: true, version: data.version ?? 1 };
      const validated = await api<CloudWorkflow>('/settings/workflows/validate', json('POST', draft));
      addWorkflow(validated);
      setMessage('已导入草稿，请检查参数映射后保存设置');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  return <section className="generation-profiles">
    <div className="profile-heading"><div><h3>{mode === 'text' ? '文本服务商' : '云端工作流'}</h3><p className="muted">{mode === 'text' ? '每个服务商独立保存密钥，可添加多个模型。' : '在图片、视频节点中选择工作流。自定义工作流通过 RunningHub 运行。'}</p></div>
      <button disabled={busy} onClick={() => mode === 'text' ? addService() : addWorkflow()}><Plus size={14}/>{mode === 'text' ? '添加文本服务' : '添加工作流'}</button></div>
    {mode === 'workflows' && <label className="workflow-import"><Upload size={14}/>导入工作流配置 JSON<input disabled={busy} aria-label="导入云端工作流" type="file" accept=".json,application/json" onChange={e => { const file = e.target.files?.[0]; if (file) void importWorkflow(file); e.target.value = ''; }}/></label>}
    <div className="profile-layout" inert={busy}><div className="profile-list" aria-label={mode === 'text' ? '文本服务列表' : '工作流列表'}>
      {(mode === 'text' ? services : workflows).map(item => <button key={item.id} aria-pressed={selected === item.id} onClick={() => choose(item.id)}><strong>{item.name || '未命名'}</strong><small>{item.id.startsWith('builtin-') ? '内置' : item.enabled ? '已启用' : '已停用'}</small></button>)}
      {mode === 'text' && !services.length && <p className="muted">添加服务商后，可在节点中选择它的模型。原默认服务仍可使用。</p>}
    </div><div className="profile-editor">
      {mode === 'text' && service && <>
        <div className="field-row"><label>服务名称<input aria-label="服务名称" value={service.name} onChange={e => updateService({ name: e.target.value })}/></label><label className="check-row"><input type="checkbox" checked={service.enabled} onChange={e => updateService({ enabled: e.target.checked })}/>启用此服务</label></div>
        <label>服务地址<input aria-label="服务地址" placeholder="https://服务商/v1" value={service.baseUrl} onChange={e => updateService({ baseUrl: e.target.value })}/><small>兼容 Chat Completions；不包含 /chat/completions。</small></label>
        <fieldset><legend>可选模型</legend>{service.models.map((model, index) => <div className="profile-model-row" key={index}><input aria-label={`模型 ${index + 1}`} value={model} placeholder="服务商提供的模型 ID" onChange={e => updateService({ models: service.models.map((m, i) => i === index ? e.target.value : m), defaultModel: service.defaultModel === model ? e.target.value : service.defaultModel })}/><button aria-label={`移除模型 ${index + 1}`} disabled={service.models.length === 1} onClick={() => { const models = service.models.filter((_, i) => i !== index); updateService({ models, defaultModel: models.includes(service.defaultModel) ? service.defaultModel : models[0] }); }}><Trash2 size={14}/></button></div>)}<button onClick={() => updateService({ models: [...service.models, ''] })}><Plus size={14}/>添加模型</button></fieldset>
        <label>默认模型<select aria-label="默认模型" value={service.defaultModel} onChange={e => updateService({ defaultModel: e.target.value })}>{service.models.map((model, i) => <option key={i} value={model}>{model || '请填写模型名称'}</option>)}</select></label>
        <label>此服务的 API 密钥<input aria-label="此服务的 API 密钥" type="password" autoComplete="new-password" value={secret} placeholder={config.credentials['text-' + service.id]?.configured ? '已配置，输入可替换' : '输入此服务的密钥'} onChange={e => setSecret(e.target.value)}/></label>
        <div className="profile-actions"><button disabled={busy || !secret.trim() || !config.vaultAvailable} onClick={() => void credential()}>保存此服务密钥</button><button disabled={busy || !config.credentials['text-' + service.id]?.configured} onClick={() => void credential(true)}>撤销此服务密钥</button></div>
        <small>保存密钥会先保存当前设置。报价键：{`text/${service.id}/模型名`}</small>
        <div><button onClick={() => { patch({ textServices: services.filter(s => s.id !== selected) }); choose(''); setMessage('已从草稿移除，保存设置后生效；可用“恢复已保存设置”撤回'); }}><Trash2 size={14}/>移除此服务配置</button><small>不会自动撤销系统密钥。若不再使用，可先撤销密钥再移除配置。</small></div>
      </>}
      {mode === 'workflows' && workflow && <>
        <div className="profile-heading"><strong>{readonly ? '内置工作流' : '编辑工作流'}</strong><button onClick={() => addWorkflow(workflow)}><Copy size={14}/>复制工作流</button></div>
        {readonly ? <p className="muted">{workflow.name}，由 generate_tool 提供。复制后可命名为自己的配置，单独设置报价。</p> : <>
          <div className="field-row"><label>工作流名称<input aria-label="工作流名称" value={workflow.name} onChange={e => updateWorkflow({ name: e.target.value })}/></label><label className="check-row"><input type="checkbox" checked={workflow.enabled} onChange={e => updateWorkflow({ enabled: e.target.checked })}/>启用此工作流</label></div>
          <label>适用节点<select aria-label="工作流适用节点" value={workflow.kinds.join(',')} onChange={e => updateWorkflow({ kinds: e.target.value.split(',') })}>{Object.entries(KIND_NAMES).map(([kind, name]) => <option key={kind} value={kind}>{name}</option>)}<option value="image.generate,image.variation,image.character,image.location">全部图片节点（含角色与场景）</option><option value="image.generate,image.variation,image.character">全部图片节点（含角色图）</option><option value="image.generate,image.variation">生成图片与图片变体</option></select></label>
          <label>工作流模板<select aria-label="工作流模板" value={workflow.builtin || 'custom'} onChange={e => { const value = e.target.value; const next: CloudWorkflow = { id: workflow.id, name: workflow.name, kinds: workflow.kinds, enabled: workflow.enabled, version: workflow.version + 1 }; if (value === 'custom') Object.assign(next, { workflow: '{}', workflowId: '', nodeInfoList: [], mappings: [{ source: 'prompt', nodeId: '', fieldName: 'text' }], resultNodes: [''] }); else { const builtin = builtins.find(b => b.builtin === value)!; Object.assign(next, { builtin: value, kinds: builtin.kinds }); } patch({ cloudWorkflows: config.cloudWorkflows.map(w => w.id === selected ? next : w) }); }}><option value="custom">自定义 RunningHub 工作流</option>{builtins.map(b => <option key={b.id} value={b.builtin}>{b.name}</option>)}</select></label>
          {!workflow.builtin && <>
            <label>提交方式<select aria-label="工作流提交方式" value={workflow.workflow === undefined ? 'id' : 'full'} onChange={e => switchSubmission(e.target.value === 'full')}><option value="full">完整工作流 JSON</option><option value="id">云端工作流 ID（兼容已有配置）</option></select></label>
            {workflow.workflow !== undefined && <label>完整工作流 JSON<textarea aria-label="完整工作流 JSON" rows={14} spellCheck={false} value={typeof workflow.workflow === 'string' ? workflow.workflow : JSON.stringify(workflow.workflow, null, 2)} onChange={e => updateWorkflow({ workflow: e.target.value })}/><small>使用 API 格式：节点 ID 对应包含 class_type、inputs 的对象。输入映射会替换对应 inputs 字段，其余节点和连接原样提交。下方工作流 ID 可留空，使用脚本默认占位值。</small></label>}
            <div className="field-row"><label>RunningHub 工作流 ID<input aria-label="RunningHub 工作流 ID" value={workflow.workflowId || ''} onChange={e => updateWorkflow({ workflowId: e.target.value })}/></label><label>配置版本<input aria-label="工作流配置版本" type="number" min={1} value={workflow.version} onChange={e => updateWorkflow({ version: Number(e.target.value) })}/></label></div>
            <fieldset><legend>输入映射</legend><small>填写云端工作流中的节点 ID 和字段名。参考素材序号从 1 开始。</small>
              {(workflow.mappings || []).map((mapping, index) => { const edit = (value: Partial<WorkflowMapping>) => updateWorkflow({ mappings: workflow.mappings!.map((m, i) => i === index ? { ...m, ...value } : m) }); return <div className="workflow-mapping" key={index}>
                <label>来源<select aria-label={`映射 ${index + 1} 来源`} value={mapping.source} onChange={e => edit({ source: e.target.value as WorkflowMapping['source'] })}>{Object.entries(SOURCES).map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label>
                <label>节点 ID<input aria-label={`映射 ${index + 1} 节点`} value={mapping.nodeId} onChange={e => edit({ nodeId: e.target.value })}/></label><label>字段名<input aria-label={`映射 ${index + 1} 字段`} value={mapping.fieldName} onChange={e => edit({ fieldName: e.target.value })}/></label>
                {['image', 'video', 'audio'].includes(mapping.source) && <><label>素材序号<input type="number" min={1} max={Math.min(...workflow.kinds.map(kind => kind === 'video.image_to_video' ? mapping.source === 'image' ? 9 : 3 : 8), 9)} value={(mapping.index || 0) + 1} onChange={e => edit({ index: Number(e.target.value) - 1 })}/></label><label className="check-row"><input type="checkbox" checked={mapping.required !== false} onChange={e => edit({ required: e.target.checked })}/>必填</label></>}
                <button aria-label={`移除映射 ${index + 1}`} onClick={() => updateWorkflow({ mappings: workflow.mappings!.filter((_, i) => i !== index) })}><Trash2 size={14}/></button>
              </div>; })}<button onClick={() => updateWorkflow({ mappings: [...(workflow.mappings || []), { source: 'prompt', nodeId: '', fieldName: '' }] })}><Plus size={14}/>添加输入映射</button></fieldset>
            <fieldset><legend>固定参数</legend>{(workflow.nodeInfoList || []).map((entry, index) => { const edit = (value: Partial<typeof entry>) => updateWorkflow({ nodeInfoList: workflow.nodeInfoList!.map((n, i) => i === index ? { ...n, ...value } : n) }); return <div className="workflow-mapping" key={index}><label>节点 ID<input value={entry.nodeId} onChange={e => edit({ nodeId: e.target.value })}/></label><label>字段名<input value={entry.fieldName} onChange={e => edit({ fieldName: e.target.value })}/></label><label>固定值<input value={String(entry.fieldValue)} onChange={e => edit({ fieldValue: e.target.value })}/></label><button aria-label={`移除固定参数 ${index + 1}`} onClick={() => updateWorkflow({ nodeInfoList: workflow.nodeInfoList!.filter((_, i) => i !== index) })}><Trash2 size={14}/></button></div>; })}<button onClick={() => updateWorkflow({ nodeInfoList: [...(workflow.nodeInfoList || []), { nodeId: '', fieldName: '', fieldValue: '' }] })}><Plus size={14}/>添加固定参数</button></fieldset>
            <fieldset><legend>输出节点</legend>{(workflow.resultNodes || []).map((id, index) => <div className="profile-model-row" key={index}><input aria-label={`输出节点 ${index + 1}`} value={id} onChange={e => updateWorkflow({ resultNodes: workflow.resultNodes!.map((n, i) => i === index ? e.target.value : n) })}/><button aria-label={`移除输出节点 ${index + 1}`} onClick={() => updateWorkflow({ resultNodes: workflow.resultNodes!.filter((_, i) => i !== index) })}><Trash2 size={14}/></button></div>)}<button onClick={() => updateWorkflow({ resultNodes: [...(workflow.resultNodes || []), ''] })}><Plus size={14}/>添加输出节点</button></fieldset>
          </>}
        </>}
        <small>报价键：{`workflow/${workflow.id}`}。保存设置后即可在对应节点中选择。</small>
        {!readonly && <div><button disabled={busy} onClick={() => void checkWorkflow()}>检查当前工作流</button><small>仅检查当前配置的格式、映射和输出节点；不会保存设置或调用云端生成。</small></div>}
        {!readonly && <div><button onClick={() => { patch({ cloudWorkflows: config.cloudWorkflows.filter(w => w.id !== selected) }); choose(''); setMessage('已从草稿移除，保存设置后生效；已排队任务保留原工作流'); }}><Trash2 size={14}/>移除此工作流配置</button><small>保存后，引用此配置的节点需重新选择工作流。</small></div>}
      </>}
      {!(mode === 'text' ? service : workflow) && <p className="profile-empty">选择左侧配置进行编辑，或添加新的{mode === 'text' ? '文本服务商' : '工作流'}。</p>}
    </div></div>
    {error && <p className="error-box" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
  </section>;
}
