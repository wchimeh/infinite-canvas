import { useStudio } from './store';

export function ShotSelection({ nodeId }: { nodeId: string }) {
  const s = useStudio();
  const node = s.nodes.find(item => item.id === nodeId);
  if (!node) return null;
  const sourceId = s.edges.find(edge => edge.target === nodeId && edge.targetHandle === 'text' && edge.data?.kind !== 'sequence')?.source;
  const source = s.nodes.find(item => item.id === sourceId);
  const task = s.tasks.filter(item => item.node_id === sourceId).sort((a, b) => b.created_at - a.created_at)[0];
  const available = task?.status === 'completed' && source?.data.status !== 'dirty';
  const shots = available ? task.output.shots || [] : [];
  const config = node.data.config;
  const selected = typeof config.shotIndex === 'number' ? shots[config.shotIndex] : undefined;
  const valid = !!selected && JSON.stringify(selected) === JSON.stringify(config.selectedShot)
    && Number.isInteger(selected.durationMs) && selected.durationMs >= 4000 && selected.durationMs <= 15000;
  const running = s.tasks.some(item => item.node_id === nodeId && ['queued', 'running', 'cancel_requested'].includes(item.status));
  return <div className="shot-selection nodrag nowheel">
    <label>选择分镜<select aria-label="选择分镜" value={valid ? String(config.shotIndex) : ''} disabled={!shots.length || running}
      onChange={event => {
        const index = Number(event.target.value), shot = shots[index];
        if (!shot) return;
        s.patch(nodeId, { config: { ...config, shotIndex: index, selectedShot: structuredClone(shot), seconds: shot.durationMs / 1000 } });
      }}>
      <option value="" disabled>请选择一条分镜…</option>
      {shots.map((shot, index) => <option key={index} value={index} disabled={!Number.isInteger(shot.durationMs) || shot.durationMs < 4000 || shot.durationMs > 15000}>
        {index + 1}. {shot.title || `分镜 ${index + 1}`} · {shot.durationMs / 1000} 秒
      </option>)}
    </select></label>
    {!sourceId ? <small>连接“提取分镜”的文本输出，再选择一条分镜。</small>
      : !shots.length ? <small>请先运行上游“提取分镜”，生成每条 4–15 秒的分镜列表。</small>
      : config.selectedShot && !valid ? <small className="choice-error">原分镜已变化或时长不合规，请重新选择。</small>
      : !valid ? <small>每个节点选择一条分镜；可添加多个选择节点。</small> : null}
    {valid && <div className="node-result-text"><small>{selected.shotSize || '分镜'} · {selected.durationMs / 1000} 秒</small>
      <p>{selected.visualPrompt}</p>{selected.dialogue && <p>对白：{selected.dialogue}</p>}
      {selected.cameraMove && <p>镜头：{selected.cameraMove}</p>}
    </div>}
  </div>;
}
