import { memo, useEffect, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { ReactFlow, Background, Controls, MiniMap, Handle, Position, ViewportPortal, applyNodeChanges, applyEdgeChanges, useReactFlow, useUpdateNodeInternals, type NodeProps } from '@xyflow/react';
import { FileText, Image, Film, AudioLines, UserRound, MapPin, Plus } from 'lucide-react';
import { useStudio } from './store';
import { VideoDuration } from './VideoDuration';
import { ShotSelection } from './ShotSelection';
import { mediaUrl, thumbnailUrl } from './api';
import { STATUS, type StudioNode, type StudioEdge } from './types';

const iconFor = (kind: string) => kind.startsWith('video') || kind === 'asset.video' ? Film : kind.includes('audio') ? AudioLines : kind.startsWith('character') ? UserRound : kind.startsWith('location') ? MapPin : kind.includes('image') ? Image : FileText;

const StudioCard = memo(({ id, data, selected }: NodeProps<StudioNode>) => {
  const def = useStudio(s => s.definitions[data.kind]);
  const video = data.kind === 'video.image_to_video';
  const counts = useStudio(useShallow(s => Object.fromEntries([['image', 9], ['audio', 3], ['video', 3]].map(([port, limit]) => [port, Math.min(Number(limit), 1 + Math.max(0, ...s.edges.filter(edge => edge.target === id && edge.data?.kind !== 'sequence' && new RegExp(`^${port}[2-9]?$`).test(edge.targetHandle || '')).map(edge => Number(edge.targetHandle?.slice(5) || 1))))]))));
  const updateInternals = useUpdateNodeInternals();
  useEffect(() => { if (video) updateInternals(id); }, [id, video, counts.image, counts.audio, counts.video, updateInternals]);
  const task = useStudio(s => s.tasks.find(t => t.node_id === id));
  const adopted = data.config.assetId || (data.status !== 'dirty' && task?.status === 'completed' ? task.output.assets?.[0] : undefined);
  const asset = useStudio(s => s.assets.find(a => a.id === adopted));
  const status = task && ['queued', 'running', 'cancel_requested'].includes(task.status) ? task.status : data.status === 'dirty' ? 'dirty' : task?.status || data.status || 'idle';
  const Icon = iconFor(data.kind);
  return <div className={`studio-node ${selected ? 'selected' : ''}`}>
    <header><Icon size={15}/><strong>{data.title}</strong><span className="node-type">{def?.displayName}</span></header>
    {!!data.groupId && <span className="node-group-label">{String(data.groupTitle || '镜头组')}</span>}
    <div className="node-body">
      {data.kind === 'shots.select' ? <ShotSelection nodeId={id}/> : asset?.mime.startsWith('image/') ? <img loading="lazy" src={thumbnailUrl(asset.id)} alt={asset.name}/> : asset?.mime.startsWith('video/') ? <video className="nodrag" src={mediaUrl(asset.id)} controls preload="metadata"/> : asset?.mime.startsWith('audio/') ? <audio className="nodrag" src={mediaUrl(asset.id)} controls preload="metadata"/> : task?.output.text ? <div className="node-result-text nodrag nowheel"><small>{status === 'dirty' ? '上次运行结果' : '文本结果'}</small><p>{task.output.text}</p></div> : <div className="node-placeholder"><Icon size={28} strokeWidth={1}/><p>{data.config.assetId ? '引用素材已缺失' : data.config.prompt || '在右侧设置内容与参考素材'}</p></div>}
    </div>

    {video && <VideoDuration seconds={data.config.seconds} onChange={seconds => useStudio.getState().patch(id, { config: { ...data.config, seconds } })}/>}
    <div className="node-ports">
      <div>{Object.entries(def?.inputs || {}).filter(([name, type]) => !video || type === 'text' || Number(name.slice(5) || 1) <= counts[type]).map(([name, type]) => <div key={name} className={'port ' + type}><Handle type="target" position={Position.Left} id={name}/><span>{video && type !== 'text' ? `${({ image: '参考图', video: '参考视频', audio: '参考音频' } as Record<string, string>)[type]} ${name.slice(5) || 1}` : ({ text: '文本', image: '参考图', video: '视频', audio: '声音' } as Record<string, string>)[type]}</span></div>)}</div>
      <div>{Object.entries(def?.outputs || {}).map(([name, type]) => <div key={name} className={'port output ' + type}><span>{({ text: '文本', image: '图片', video: '视频', audio: '声音' } as Record<string, string>)[type]}</span><Handle type="source" position={Position.Right} id={name}/></div>)}</div>
    </div>
    <footer><span className={'status-dot ' + status}/>{STATUS[status]}{task?.reused ? ' · 缓存复用' : ''}{task?.external_id && status === 'queued' ? ' · 已提交云端' : ''}</footer>
  </div>;
});
const nodeTypes = { studio: StudioCard };

export function Canvas({ notice }: { notice: (text: string) => void }) {
  const s = useStudio(useShallow(state => ({ nodes: state.nodes, edges: state.edges, definitions: state.definitions, viewport: state.viewport,
    replace: state.replace, add: state.add, connect: state.connect, checkpoint: state.checkpoint, group: state.group, ungroup: state.ungroup })));
  const flow = useReactFlow<StudioNode>();
  const rememberClick = (event: { clientX: number; clientY: number }) => {
    useStudio.setState({ insertionPosition: flow.screenToFlowPosition({ x: event.clientX, y: event.clientY }) });
  };
  const focusRequest = useStudio(state => state.focusRequest);
  useEffect(() => {
    if (!focusRequest) return;
    useStudio.setState({ focusRequest: null });
    const node = useStudio.getState().nodes.find(n => n.id === focusRequest.nodeId);
    if (!node) return;
    void flow.setCenter(node.position.x + (node.measured?.width || 280) / 2,
      node.position.y + (node.measured?.height || 320) / 2,
      { zoom: Math.min(1, flow.getZoom() < 0.5 ? 0.8 : flow.getZoom()), duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 200 });
    document.querySelector('.canvas-area')?.scrollIntoView({ block: 'nearest' });
  }, [focusRequest, flow]);
  const groups = useMemo(() => {
    const values = new Map<string, { id: string; title: string; x: number; y: number; right: number; bottom: number }>();
    for (const node of s.nodes) {
      const id = node.data.groupId; if (typeof id !== 'string') continue;
      const previous = values.get(id), x = node.position.x - 18, y = node.position.y - 36;
      const right = node.position.x + (node.measured?.width || 280) + 18, bottom = node.position.y + (node.measured?.height || 260) + 18;
      values.set(id, { id, title: String(node.data.groupTitle || '镜头组'), x: Math.min(previous?.x ?? x, x), y: Math.min(previous?.y ?? y, y), right: Math.max(previous?.right ?? right, right), bottom: Math.max(previous?.bottom ?? bottom, bottom) });
    }
    return [...values.values()];
  }, [s.nodes]);
  return <div className="canvas-area" onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }} onDrop={e => {
    e.preventDefault(); const kind = e.dataTransfer.getData('application/canvas-kind');
    if (s.definitions[kind]) s.add(kind, flow.screenToFlowPosition({ x: e.clientX, y: e.clientY }));
  }}>
    <ReactFlow<StudioNode, StudioEdge> nodes={s.nodes} edges={s.edges} nodeTypes={nodeTypes} defaultViewport={s.viewport}
      onPaneClick={rememberClick} onNodeClick={rememberClick} onEdgeClick={rememberClick}
      onNodesChange={changes => s.replace(applyNodeChanges(changes, s.nodes), s.edges, changes.some(c => c.type !== 'select' && c.type !== 'dimensions'))}
      onEdgesChange={changes => s.replace(s.nodes, applyEdgeChanges(changes, s.edges), changes.some(c => c.type !== 'select'))}
      onNodeDragStart={s.checkpoint}
      onConnect={c => { const error = s.connect({ ...c, id: crypto.randomUUID(), data: { kind: 'data' } }); if (error) notice(error); }}
      onMoveEnd={(_, viewport) => useStudio.setState(state => ({ viewport, edits: state.edits + 1 }))}
      onNodeContextMenu={(event, node) => {
        event.preventDefault();
        if (!s.definitions[node.data.kind]?.outputs.image) { notice('可对图片节点右键，创建关联的生成视频节点'); return; }
        const id = s.add('video.image_to_video', { x: node.position.x + 340, y: node.position.y }, { seconds: 5 });
        s.connect({ id: crypto.randomUUID(), source: node.id, sourceHandle: 'image', target: id, targetHandle: 'image', data: { kind: 'data' } });
      }}
      deleteKeyCode={null} selectionOnDrag panOnDrag={[1, 2]} panActivationKeyCode="Space" multiSelectionKeyCode="Shift" selectionKeyCode="Shift"
      onlyRenderVisibleElements colorMode="light" minZoom={0.15} maxZoom={2.5}>
      <ViewportPortal>{groups.map(group => <div className="canvas-group" data-groupid={group.id} key={group.id} style={{ transform: `translate(${group.x}px,${group.y}px)`, width: group.right - group.x, height: group.bottom - group.y }}><span>{group.title}</span></div>)}</ViewportPortal>
      <Background gap={24} size={1}/><Controls showInteractive={false}/><MiniMap pannable zoomable nodeColor="#739d97" maskColor="rgba(235,241,243,.75)"/>
    </ReactFlow>
    {!s.nodes.length && <div className="canvas-empty"><span className="eyebrow">从一个故事开始</span><h2>把灵感，连成镜头。</h2><p>添加故事、参考图与生成节点，<br/>在画布上组织你的第一部短剧。</p><button className="primary" onClick={() => s.add('story.prompt')}><Plus size={16}/>添加故事节点</button><small>也可以从左侧拖入节点</small></div>}
    <div className="canvas-group-actions"><button aria-label="组合选中节点" disabled={s.nodes.filter(n => n.selected).length < 2} onClick={() => { s.group(); notice('选中节点已组合，分组不改变生成依赖'); }}>组合</button><button aria-label="解组选中节点" disabled={!s.nodes.some(n => n.selected && n.data.groupId)} onClick={s.ungroup}>解组</button><button aria-label="选择同组节点" disabled={!s.nodes.some(n => n.selected && n.data.groupId)} onClick={() => { const groups = new Set(s.nodes.filter(n => n.selected).map(n => n.data.groupId).filter(Boolean)); s.replace(s.nodes.map(n => ({ ...n, selected: groups.has(n.data.groupId) })), s.edges, false); }}>选中同组</button></div>
    <div className="canvas-hint">空格 + 拖动平移 <span>·</span> Shift 框选 <span>·</span> 图片节点右键生成视频</div>
  </div>;
}
