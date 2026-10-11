import { Check, Play } from 'lucide-react';
import { useState } from 'react';
import { useStudio } from './store';
import type { Config, GenerationOptions, Profile } from './types';

export function BatchGeneration({ kind, count, taskId, profiles, initialConfig, options, busy, runStage, generate }: {
  kind: 'image.character' | 'image.location'; count: number; taskId: string; profiles: Profile[];
  initialConfig: Config; options: GenerationOptions; busy: boolean; runStage: string; generate: (config: Config) => void;
}) {
  const [selection, setSelection] = useState<Config>({});
  const studio = useStudio();
  const config = { ...initialConfig, ...selection };
  const character = kind === 'image.character';
  const label = character ? '角色' : '场景';
  const key = character ? 'characterId' : 'locationId';
  const associated = profiles.filter(profile => profile.sourceKey?.startsWith(`${taskId}:`));
  const nodes = associated.map(profile => studio.nodes.find(node => node.data.kind === kind && node.data.config[key] === profile.id)).filter(node => !!node);
  const latest = nodes.map(node => studio.tasks.filter(task => task.node_id === node.id).sort((a, b) => b.created_at - a.created_at)[0]);
  const active = latest.filter(task => task && ['queued', 'running', 'cancel_requested'].includes(task.status)).length;
  const complete = nodes.filter((node, index) => node.data.config.assetId || latest[index]?.status === 'completed').length;
  const failed = latest.filter(task => task && ['failed', 'blocked', 'cancelled'].includes(task.status)).length;
  const workflows = options.workflows.filter(workflow => workflow.kinds.includes(kind));
  const selected = workflows.find(workflow => workflow.id === config.workflowId);
  const invalid = config.provider !== 'comfyui' && !!config.workflowId && !selected?.enabled;
  return <section className="batch-generation" aria-label={`${label}批量生成`}>
    <div className="batch-heading"><h3>{label}图批量生成</h3><span>{count} {character ? '个角色' : '个场景'}</span></div>
    <p>{character ? '每人一张三视图，按顺序逐张生成。' : '每处一张四视图，按媒体并发设置生成。'}</p>
    <label>生成服务<select aria-label={`批量${label}生成服务`} value={config.provider || 'runninghub'} disabled={!!active || !!runStage} onChange={event => setSelection(current => ({ ...current, provider: event.target.value as 'runninghub' | 'comfyui' }))}><option value="runninghub">RunningHub 云端</option><option value="comfyui">本地 ComfyUI</option></select></label>
    {config.provider !== 'comfyui' && <label>生成工作流<select aria-label={`批量${label}工作流`} value={config.workflowId || ''} disabled={!!active || !!runStage} onChange={event => setSelection(current => ({ ...current, workflowId: event.target.value }))}>
      <option value="">默认工作流（使用设置配置）</option>
      {!!config.workflowId && !selected && <option value={config.workflowId}>原工作流不可用，请重新选择</option>}
      {workflows.map(workflow => <option key={workflow.id} value={workflow.id} disabled={!workflow.enabled}>{workflow.name}{!workflow.enabled ? '（已停用）' : ''}</option>)}
    </select></label>}
    {invalid && <small className="choice-error">请选择可用的生成工作流。</small>}
    <div className="batch-status" role="status"><span><Check size={13}/>已完成 {complete}/{count}</span><span>排队 / 生成中 {active}</span>{failed > 0 && <span className="choice-error">未成功 {failed}</span>}</div>
    <button className="primary batch-submit" disabled={busy || !!runStage || !!active || invalid} onClick={() => generate(config)}><Play size={14}/>{runStage || (active ? `正在生成${label}…` : `生成全部${label}（${count}）`)}</button>
    <small>复用已有节点和已采用图片。查看或重新生成单张图片，请选择对应节点。</small>
  </section>;
}
