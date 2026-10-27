import { useEffect, useState } from 'react';
import { X, KeyRound, HardDrive, Gauge, Plus, Trash2, Layers3 } from 'lucide-react';
import { api, json } from './api';
import type { AppSettings, CloudWorkflow, CostSummary, Diagnostics, GenerationOptions, PriceRule, Project } from './types';
import { GenerationProfiles } from './GenerationProfiles';
import { StorageSettings } from './StorageSettings';

export function Settings({ project, changeProject, saved, close, initialTab = 'services' }: { project?: Project; changeProject: (project: Project) => void; saved: () => void; close: () => void; initialTab?: string }) {
  const [config, setConfig] = useState<AppSettings>();
  const [builtins, setBuiltins] = useState<CloudWorkflow[]>([]);
  const [generationRevision, setGenerationRevision] = useState(0);
  const [keys, setKeys] = useState({ runninghub: '', text: '' });
  const [tab, setTab] = useState(initialTab), [error, setError] = useState(''), [message, setMessage] = useState(''), [busy, setBusy] = useState(false);
  const [workflows, setWorkflows] = useState('{}'), [diagnostics, setDiagnostics] = useState<Diagnostics>();
  const [costs, setCosts] = useState<CostSummary>(), [limit, setLimit] = useState(project?.settings.budget?.limit || '');
  const [currency, setCurrency] = useState<'CNY' | 'USD'>(project?.settings.budget?.currency || 'CNY');
  const [priceName, setPriceName] = useState('runninghub/ltx23');
  useEffect(() => { let active = true; void (async () => {
    try {
      const [settings, options] = await Promise.all([api<AppSettings>('/settings'), api<GenerationOptions>('/generation-options')]);
      if (active) { setConfig(settings); setBuiltins(options.workflows.filter(w => w.id.startsWith('builtin-'))); setWorkflows(JSON.stringify(settings.comfyWorkflows, null, 2)); }
      if (project) { const summary = await api<CostSummary>(`/projects/${project.id}/costs`); if (active) setCosts(summary); }
    } catch (e) { if (active) setError(e instanceof Error ? e.message : String(e)); }
  })(); return () => { active = false; }; }, [project?.id]);
  async function action(work: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('');
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }
  function patch(value: Partial<AppSettings>) { setConfig(current => current ? { ...current, ...value } : current); }
  function mergeCredentials(settings: AppSettings) { patch({ credentials: settings.credentials }); }
  function price(name: string, changes: Partial<PriceRule>) { if (config) patch({ pricing: { ...config.pricing, [name]: { ...config.pricing[name], ...changes } } }); }
  const priceOptions = config ? [
    ...[...builtins, ...config.cloudWorkflows].map(w => ({ key: `workflow/${w.id}`, label: `工作流 / ${w.name}` })),
    ...config.textServices.flatMap(s => s.models.filter(Boolean).map(model => ({ key: `text/${s.id}/${model}`, label: `${s.name} / ${model}` }))),
    ...(config.textModel ? [{ key: `text/${config.textModel}`, label: `默认文本服务 / ${config.textModel}` }] : []),
  ] : [];
  async function restore() {
    const [settings, options, currentProject] = await Promise.all([
      api<AppSettings>('/settings'), api<GenerationOptions>('/generation-options'), project ? api<Project>(`/projects/${project.id}`) : Promise.resolve(undefined),
    ]);
    setConfig(settings); setBuiltins(options.workflows.filter(w => w.id.startsWith('builtin-')));
    setWorkflows(JSON.stringify(settings.comfyWorkflows, null, 2)); setKeys({ runninghub: '', text: '' });
    setDiagnostics(undefined); setGenerationRevision(value => value + 1);
    if (currentProject) { setLimit(currentProject.settings.budget?.limit || ''); setCurrency(currentProject.settings.budget?.currency || 'CNY'); changeProject(currentProject); }
    saved(); setMessage('已恢复保存的设置，未保存的修改已撤回');
  }
  async function save() {
    if (!config) return;
    if (!Number.isInteger(config.canvasPreviewThreshold) || config.canvasPreviewThreshold < 10 || config.canvasPreviewThreshold > 100) throw new Error('隐藏预览的缩放阈值须为10–100的整数百分比');
    const parsed: unknown = JSON.parse(workflows);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('本地工作流配置必须是 JSON 对象');
    const settings = await api<AppSettings>('/settings', json('PUT', { textApiBase: config.textApiBase, textModel: config.textModel, comfyUrl: config.comfyUrl,
      comfyWorkflows: parsed, concurrency: config.concurrency, pricing: config.pricing, textServices: config.textServices, cloudWorkflows: config.cloudWorkflows, confirmGenerationCost: config.confirmGenerationCost !== false,
      canvasHidePreviews: config.canvasHidePreviews, canvasPreviewThreshold: config.canvasPreviewThreshold }));
    setConfig(settings);
    if (project) changeProject(await api<Project>(`/projects/${project.id}/settings`, json('PUT', { budget: limit.trim() ? { limit, currency } : null })));
    saved(); setMessage('设置已保存');
  }
  return <div className="modal-backdrop"><section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
    <header><div><h2 id="settings-title">工作台设置</h2><p>服务凭据保存在系统中，项目可以独立迁移。</p></div><button aria-label="关闭设置" onClick={close}><X size={18}/></button></header>
    <nav className="settings-tabs" aria-label="设置分类">{[['services', '生成服务', KeyRound], ['workflows', '云端工作流', Layers3], ['local', '本地模型', HardDrive], ['budget', '费用与并发', Gauge], ['canvas', '画布显示', Layers3], ['storage', '数据存储', HardDrive]].map(([id, title, Icon]) => {
      const TabIcon = Icon as typeof KeyRound; return <button key={id as string} className={tab === id ? 'active' : ''} onClick={() => setTab(id as string)}><TabIcon size={15}/>{title as string}</button>;
    })}</nav>
    <div className="settings-body">{!config ? <p>{error || '正在读取设置…'}</p> : <>
      {tab === 'storage' && <StorageSettings/>}
      {tab === 'canvas' && <section><h3>缩放与预览</h3>
        <label className="check-row" style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}><input type="checkbox" checked={config.canvasHidePreviews} disabled={busy} onChange={e => patch({ canvasHidePreviews: e.target.checked })}/>缩小时隐藏节点预览</label>
        <label>隐藏预览的缩放阈值（%）<input aria-label="隐藏预览的缩放阈值" type="number" min={10} max={100} step={1} value={config.canvasPreviewThreshold} disabled={busy || !config.canvasHidePreviews} onChange={e => patch({ canvasPreviewThreshold: Number(e.target.value) })}/></label>
        <p className="muted">缩放低于此比例时隐藏节点内容，放大至该比例恢复。默认50%，可设置10%–100%。关闭后始终显示预览，大画布可能更占性能。</p>
        <small>点击“保存设置”后立即生效，适用于本机所有项目。</small>
      </section>}
      {tab === 'services' && <><section><h3>RunningHub</h3><p className="muted">图片、视频与音频生成。密钥保存后只显示配置状态。</p><div className="credential-row"><input aria-label="RunningHub 密钥" type="password" autoComplete="new-password" value={keys.runninghub} placeholder={config.credentials.runninghub.configured ? '已配置，输入可替换' : '输入 API 密钥'} onChange={e => setKeys({ ...keys, runninghub: e.target.value })}/><button disabled={busy || !keys.runninghub.trim() || !config.vaultAvailable} onClick={() => void action(async () => { mergeCredentials(await api<AppSettings>('/settings/credentials/runninghub', json('PUT', { key: keys.runninghub }))); setKeys({ ...keys, runninghub: '' }); saved(); setMessage('RunningHub 凭据已保存在系统中'); })}>保存密钥</button><button disabled={busy || !config.credentials.runninghub.configured} onClick={() => void action(async () => { mergeCredentials(await api<AppSettings>('/settings/credentials/runninghub', { method: 'DELETE' })); saved(); setMessage('系统凭据已撤销'); })}>撤销</button></div><small>{config.credentials.runninghub.source === 'environment' ? '当前使用环境变量；撤销系统记录不会移除环境变量。' : config.credentials.runninghub.configured ? '系统凭据已配置' : '尚未配置'}</small></section>
      <section><h3>文本服务</h3><div className="field-row"><label>服务地址<input aria-label="文本服务地址" placeholder="https://服务商/v1" value={config.textApiBase} onChange={e => patch({ textApiBase: e.target.value })}/></label><label>模型名称<input aria-label="文本模型名称" value={config.textModel} onChange={e => patch({ textModel: e.target.value })}/></label></div><div className="credential-row"><input aria-label="文本服务密钥" type="password" autoComplete="new-password" value={keys.text} placeholder={config.credentials.text.configured ? '已配置，输入可替换' : '输入 API 密钥'} onChange={e => setKeys({ ...keys, text: e.target.value })}/><button disabled={busy || !keys.text.trim() || !config.vaultAvailable} onClick={() => void action(async () => { mergeCredentials(await api<AppSettings>('/settings/credentials/text', json('PUT', { key: keys.text }))); setKeys({ ...keys, text: '' }); saved(); setMessage('文本服务凭据已保存在系统中'); })}>保存密钥</button><button disabled={busy || !config.credentials.text.configured} onClick={() => void action(async () => { mergeCredentials(await api<AppSettings>('/settings/credentials/text', { method: 'DELETE' })); saved(); setMessage('系统凭据已撤销'); })}>撤销</button></div><small>兼容 Chat Completions；地址包含 /v1 等前缀，不包含 /chat/completions。</small></section>
      <GenerationProfiles key={`text-${generationRevision}`} mode="text" config={config} patch={patch} builtins={builtins} save={save} saved={saved}/>
      {!config.vaultAvailable && <p className="error-box">此平台尚无系统凭据适配；默认服务可通过环境变量配置，新服务的独立密钥请在 Windows 下保存。</p>}</>}
      {tab === 'workflows' && <GenerationProfiles key={`workflows-${generationRevision}`} mode="workflows" config={config} patch={patch} builtins={builtins} save={save} saved={saved}/>}
      {tab === 'local' && <><section><h3>ComfyUI</h3><p className="muted">连接已安装的本机运行时。在节点属性中选择「本地 ComfyUI」即可保持本地生成。</p><label>本地服务地址<input aria-label="ComfyUI 服务地址" value={config.comfyUrl} onChange={e => patch({ comfyUrl: e.target.value })}/></label><button disabled={busy} onClick={() => void action(async () => { await save(); setDiagnostics(await api<Diagnostics>('/settings/diagnostics')); })}>保存并检测本地环境</button></section>
      {diagnostics && <section className="diagnostic-results"><h3>环境检测</h3><p>FFmpeg：{diagnostics.ffmpeg ? '可用' : '未找到'} · 剩余磁盘：{(diagnostics.diskFreeBytes / 1024 ** 3).toFixed(1)} GB</p><p>ComfyUI：{diagnostics.comfyui.ready ? `已连接 · ${diagnostics.comfyui.nodeCount} 种节点` : diagnostics.comfyui.error}</p>{diagnostics.comfyui.devices.map((device, i) => <p key={i}>{device.name}{device.vram_total ? ` · 显存 ${(device.vram_total / 1024 ** 3).toFixed(1)} GB` : ''}</p>)}{Object.entries(diagnostics.comfyui.workflows).map(([kind, check]) => <p key={kind}>{kind}：{check.ready ? '模板依赖就绪' : check.error}</p>)}</section>}
      <details><summary>配置本地工作流模板</summary><p className="muted">按节点类型保存版本化 API 工作流。每项包含 version、prompt 和 mappings；映射项用 node/input 指定提示词与素材输入位置。</p><label>导入工作流配置<input type="file" accept="application/json,.json" onChange={e => { const file = e.target.files?.[0]; if (file) void action(async () => { const parsed = JSON.parse(await file.text()); setWorkflows(JSON.stringify(parsed, null, 2)); setMessage('已读取配置，请保存并检测依赖'); }); }}/></label><textarea aria-label="本地工作流 JSON" className="code-editor" rows={14} value={workflows} onChange={e => setWorkflows(e.target.value)}/><small>例如 image.generate 对应一项工作流；prompt 为 ComfyUI 导出的 API 格式。模型文件与自定义节点需在 ComfyUI 中安装，检测会列出缺失项。</small></details></>}
      {tab === 'budget' && <><section><h3>项目预算</h3>{project ? <><p className="muted">{project.name} · 预算按提交前估算预留，实际费用以服务商账单为准。</p><div className="field-row"><label>预算上限<input aria-label="项目预算上限" type="number" min={0} step="0.01" placeholder="留空表示不上限" value={limit} onChange={e => setLimit(e.target.value)}/></label><label>币种<select aria-label="预算币种" value={currency} onChange={e => setCurrency(e.target.value as 'CNY' | 'USD')}><option value="CNY">CNY 人民币</option><option value="USD">USD 美元</option></select></label></div>{costs && <p>已预留估算：{Object.entries(costs.estimatedUsed).map(([unit, value]) => `${value} ${unit}`).join(' / ') || '0'}{costs.unknownCount ? ` · ${costs.unknownCount} 项费用未知` : ''}。尚无服务商结算数据。</p>}<small>启用预算后，未知模型价格或币种不匹配会阻止提交。</small></> : <p>打开项目后可以设置预算。</p>}</section>
      <section><h3>生成费用提示</h3><label className="check-row"><input type="checkbox" aria-label="生成前显示费用提示" checked={config.confirmGenerationCost !== false} onChange={e => patch({ confirmGenerationCost: e.target.checked })}/>生成前显示费用提示</label><small>关闭后，点击运行将直接提交生成任务，服务商可能收费。费用估算和项目预算限制仍然生效。保存后适用于所有项目。</small></section>
      <section><h3>模型价格</h3><p className="muted">请按服务商实际价格填写。留空模型视为费用未知，不自动假设免费。</p>
        <label>选择报价对象<select aria-label="选择报价对象" value={priceOptions.some(option => option.key === priceName) ? priceName : ''} onChange={e => setPriceName(e.target.value)}><option value="">手动填写报价键…</option>{priceOptions.map(option => <option key={option.key} value={option.key}>{option.label}</option>)}</select></label>
        <div className="price-list">{Object.entries(config.pricing).map(([name, rule]) => <div className="price-rule" key={name}>
          <strong title={name}>{priceOptions.find(option => option.key === name)?.label || name}</strong><input aria-label={`${name}单价`} type="number" min={0} step="0.000001" value={rule.amount} onChange={e => price(name, { amount: e.target.value })}/>
          <select aria-label={`${name}计费单位`} value={rule.unit} onChange={e => price(name, { unit: e.target.value as 'task' | 'second' })}><option value="task">每次任务</option><option value="second">每秒生成</option></select>
          <select aria-label={`${name}币种`} value={rule.currency} onChange={e => price(name, { currency: e.target.value as 'CNY' | 'USD' })}><option>CNY</option><option>USD</option></select>
          <button aria-label={`移除${name}价格`} onClick={() => { const pricing = { ...config.pricing }; delete pricing[name]; patch({ pricing }); }}><Trash2 size={14}/></button>
        </div>)}</div>
        <div className="field-row"><input aria-label="新价格模型" value={priceName} onChange={e => setPriceName(e.target.value)} placeholder="runninghub/ltx23"/><button disabled={!priceName.trim() || !!config.pricing[priceName.trim()]} onClick={() => patch({ pricing: { ...config.pricing, [priceName.trim()]: { amount: '', unit: 'task', currency: 'CNY' } } })}><Plus size={14}/>添加价格</button></div>
        <small>选择名称后自动填入报价键。手工输入仍支持 runninghub/ltx23、text/模型名或 image.generate 等旧配置规则。</small>
      </section>
      <section><h3>同时运行任务</h3><div className="concurrency-fields">{([['media', '图片＋视频'], ['text', 'LLM 文本'], ['audio', '音频']] as const).map(([kind, title]) => <label key={kind}>{title}<input aria-label={`${title}并发数`} type="number" min={1} max={8} value={config.concurrency[kind]} onChange={e => patch({ concurrency: { ...config.concurrency, [kind]: Number(e.target.value) } })}/></label>)}</div><small>图片和视频共用总并发额度，LLM 使用独立队列和执行线程。已提交的远端排队任务同样占用名额；降低容量会等待已有任务完成。</small></section></>}
    </>}{error && <p className="error-box" role="alert">{error}</p>}{message && <p role="status">{message}</p>}</div>
    <footer><small>{tab === 'storage' ? '数据路径通过页面中的“保存数据路径”按钮单独保存' : '配置仅保存在本机 · 密钥不会写入项目'}</small>{tab !== 'storage' && <div className="profile-actions"><button disabled={busy || !config} onClick={() => void action(restore)}>恢复已保存设置</button><button disabled={busy || !config} className="primary" onClick={() => void action(save)}>{busy ? '处理中…' : '保存设置'}</button></div>}</footer>
  </section></div>;
}
