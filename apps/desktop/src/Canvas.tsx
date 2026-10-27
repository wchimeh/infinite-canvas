import { memo, useEffect, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { ReactFlow, Background, Controls, MiniMap, Handle, Position, SelectionMode, ViewportPortal, applyNodeChanges, applyEdgeChanges, useReactFlow, useStore, useUpdateNodeInternals, type NodeProps } from '@xyflow/react';
import { FileText, Image, Film, AudioLines, UserRound, MapPin, Plus } from 'lucide-react';
import { useStudio } from './store';
import { VideoDuration } from './VideoDuration';
import { ShotSelection } from './ShotSelection';
import { InputPort, InputPortPickerProvider } from './InputPortPicker';
import { portCounts, nodeTask, indexedAsset } from './canvasIndexes';
import { mediaUrl, thumbnailUrl } from './api';
import { STATUS, type StudioNode, type StudioEdge } from './types';

const iconFor = (kind: string) => kind.startsWith('video') || kind === 'asset.video' || kind === 'frame.extract' ? Film : kind.includes('audio') ? AudioLines : kind.startsWith('character') ? UserRound : kind.startsWith('location') ? MapPin : kind.includes('image') ? Image : FileText;

const StudioCard = memo(({ id, data, selected }: NodeProps<StudioNode>) => {
  const def = useStudio(s => s.definitions[data.kind]);
  const video = ['video.image_to_video', 'video.combat'].includes(data.kind);
  const concat = data.kind === 'text.concat', character = data.kind.startsWith('image.');
  const expansion = data.kind === 'prompt.video_expand';
  const legacyAudioPorts = useStudio(s => expansion ? s.edges.reduce((mask, edge) => edge.target === id && /^audio[23]?$/.test(edge.targetHandle || '') && edge.data?.kind !== 'sequence'
    ? mask | (1 << (Number(edge.targetHandle!.slice(5) || 1) - 1)) : mask, 0) : 0);
  const counts = useStudio(s => portCounts(s.edges, id, character));
  const updateInternals = useUpdateNodeInternals();
  useEffect(() => { if (video || concat || character || expansion) updateInternals(id); }, [id, video, concat, character, expansion, counts.image, counts.audio, counts.video, counts.videoAudio, counts.text, legacyAudioPorts, updateInternals]);
  const task = useStudio(s => nodeTask(s.tasks, id));
  const resultText = data.config.editedResult?.text ?? (task?.snapshot.config.editedResult ? data.config.originalResult?.text : undefined) ?? task?.output.text;
  const adopted = data.config.assetId || (data.status !== 'dirty' && task?.status === 'completed' ? task.output.assets?.[0] : undefined);
  const asset = useStudio(s => indexedAsset(s.assets, adopted));
  const status = task && ['queued', 'running', 'cancel_requested'].includes(task.status) ? task.status : data.status === 'dirty' ? 'dirty' : task?.status || data.status || 'idle';
  const Icon = iconFor(data.kind);
  return <div className={`studio-node ${selected ? 'selected' : ''}`}>
    <header><Icon size={15}/><strong>{data.title}</strong><span className="node-type">{def?.displayName}</span></header>
    {!!data.groupId && <span className="node-group-label">{String(data.groupTitle || '镜头组')}</span>}
    {data.config.editedResult && <span className="node-group-label">已采用编辑稿</span>}
    <div className="node-body">
      {data.kind === 'shots.select' ? <ShotSelection nodeId={id}/> : asset?.mime.startsWith('image/') ? <img loading="lazy" src={thumbnailUrl(asset.id)} alt={asset.name}/> : asset?.mime.startsWith('video/') ? <video className="nodrag" src={mediaUrl(asset.id)} controls preload="metadata"/> : asset?.mime.startsWith('audio/') ? <audio className="nodrag" src={mediaUrl(asset.id)} controls preload="metadata"/> : resultText ? <div className="node-result-text nodrag nowheel"><small>{status === 'dirty' ? '上次运行结果' : '文本结果'}</small><p>{resultText}</p></div> : <div className="node-placeholder"><Icon size={28} strokeWidth={1}/><p>{data.config.assetId ? '引用素材已缺失' : data.config.prompt || '在右侧设置内容与参考素材'}</p></div>}
    </div>

    {video && <VideoDuration seconds={data.config.seconds ?? (data.kind === 'video.combat' ? 8 : undefined)} onChange={seconds => useStudio.getState().patch(id, { config: { ...data.config, seconds, durationSource: 'manual' } })}/>}
    <div className="node-ports">
      <div>{Object.entries(def?.inputs || {}).filter(([name, type]) => {
        const group = name.startsWith('videoAudio') ? 'videoAudio' : type;
        if (expansion && type === 'audio') return !!(legacyAudioPorts & (1 << (Number(name.slice(5) || 1) - 1)));
        return !((video || expansion) && type !== 'text' || character && type === 'image' || concat) || Number(name.slice(group.length) || 1) <= counts[group as keyof typeof counts];
      }).map(([name, type]) => {
        const group = name.startsWith('videoAudio') ? 'videoAudio' : type;
        const dynamic = (video || expansion) && type !== 'text' || character && type === 'image' || concat;
        const label = ({ text: '文本', image: '参考图', video: '参考视频', audio: '参考音频', videoAudio: '视频音频' } as Record<string, string>)[group];
        const portLabel = expansion && type === 'audio' ? '旧音频（不参与扩写）' : dynamic ? `${label} ${name.slice(group.length) || 1}` : label || type;
        if (expansion && type === 'audio') return <div key={name} className="port audio" title="此连线不参与扩写；请将音频连接视频生成节点"><Handle type="target" position={Position.Left} id={name} isConnectable={false} isConnectableStart={false} isConnectableEnd={false}/><span>{portLabel}</span></div>;
        return <div key={name} className={'port ' + type} title={group === 'videoAudio' ? '将录音传入工作流的视频音频输入，无参考视频也会上传' : undefined}><InputPort nodeId={id} name={name} type={type} label={portLabel}/><span>{portLabel}</span></div>;
      })}</div>
      <div>{Object.entries(def?.outputs || {}).map(([name, type]) => <div key={name} className={'port output ' + type}><span>{({ text: '文本', image: '图片', video: '视频', audio: '声音' } as Record<string, string>)[type]}</span><Handle type="source" position={Position.Right} id={name}/></div>)}</div>
    </div>
    <footer><span className={'status-dot ' + status}/>{STATUS[status]}{task?.reused ? ' · 缓存复用' : ''}{task?.external_id && status === 'queued' ? ' · 已提交云端' : ''}</footer>
  </div>;
});
const nodeTypes = { studio: StudioCard };
const defaultEdgeOptions = { interactionWidth: 32 };

export function Canvas({ notice, hidePreviews = true, previewThreshold = 50 }: { notice: (text: string) => void; hidePreviews?: boolean; previewThreshold?: number }) {
  const s = useStudio(useShallow(state => ({ nodes: state.nodes, edges: state.edges, definitions: state.definitions, viewport: state.viewport,
    replace: state.replace, add: state.add, connect: state.connect, checkpoint: state.checkpoint, group: state.group, ungroup: state.ungroup })));
  const flow = useReactFlow<StudioNode>();
  const overview = useStore(state => hidePreviews && state.transform[2] < previewThreshold / 100);
  const displayEdges = useMemo(() => {
    const selected = new Set(s.nodes.filter(node => node.selected).map(node => node.id));
    return s.edges.map(edge => selected.has(edge.source) || selected.has(edge.target)
      ? { ...edge, className: [edge.className, 'node-connected-highlight'].filter(Boolean).join(' ') }
      : edge);
  }, [s.nodes, s.edges]);
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
  return <InputPortPickerProvider><div className={`canvas-area${overview ? ' canvas-overview' : ''}`} onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }} onDrop={e => {
    e.preventDefault(); const kind = e.dataTransfer.getData('application/canvas-kind');
    if (s.definitions[kind]) s.add(kind, flow.screenToFlowPosition({ x: e.clientX, y: e.clientY }));
  }}>
    <ReactFlow<StudioNode, StudioEdge> nodes={s.nodes} edges={displayEdges} nodeTypes={nodeTypes} defaultViewport={s.viewport}
      connectionRadius={32} defaultEdgeOptions={defaultEdgeOptions}
      onPaneClick={rememberClick} onNodeClick={rememberClick} onEdgeClick={rememberClick}
      onNodesChange={changes => { const current = useStudio.getState(); current.replace(applyNodeChanges(changes, current.nodes), current.edges, changes.some(c => c.type !== 'select' && c.type !== 'dimensions')); }}
      onEdgesChange={changes => { const current = useStudio.getState(); current.replace(current.nodes, applyEdgeChanges(changes, current.edges), changes.some(c => c.type !== 'select')); }}
      onNodeDragStart={s.checkpoint}
      onSelectionDragStart={s.checkpoint}
      onConnect={c => { const error = s.connect({ ...c, id: crypto.randomUUID(), data: { kind: 'data' } }); if (error) notice(error); }}
      onMoveEnd={(_, viewport) => useStudio.setState(state => ({ viewport, edits: state.edits + 1 }))}
      onNodeContextMenu={(event, node) => {
        event.preventDefault();
        if (!s.definitions[node.data.kind]?.outputs.image) { notice('可对图片节点右键，创建关联的生成视频节点'); return; }
        const id = s.add('video.image_to_video', { x: node.position.x + 340, y: node.position.y }, { seconds: 5 });
        s.connect({ id: crypto.randomUUID(), source: node.id, sourceHandle: 'image', target: id, targetHandle: 'image', data: { kind: 'data' } });
      }}
      deleteKeyCode={null} selectionOnDrag selectionMode={SelectionMode.Partial} panOnDrag={[1, 2]} panActivationKeyCode="Space" multiSelectionKeyCode={['Control', 'Meta', 'Shift']} selectionKeyCode="Shift"
      onlyRenderVisibleElements colorMode="light" minZoom={0.15} maxZoom={2.5}>
      <ViewportPortal>{groups.map(group => <div className="canvas-group" data-groupid={group.id} key={group.id} style={{ transform: `translate(${group.x}px,${group.y}px)`, width: group.right - group.x, height: group.bottom - group.y }}><span>{group.title}</span></div>)}</ViewportPortal>
      <Background gap={24} size={1}/><Controls showInteractive={false}/><MiniMap pannable zoomable nodeColor="#739d97" maskColor="rgba(235,241,243,.75)"/>
    </ReactFlow>
    {!s.nodes.length && <div className="canvas-empty"><span className="eyebrow">从一个故事开始</span><h2>把灵感，连成镜头。</h2><p>添加故事、参考图与生成节点，<br/>在画布上组织你的第一部短剧。</p><button className="primary" onClick={() => s.add('story.prompt')}><Plus size={16}/>添加故事节点</button><small>也可以从左侧拖入节点</small></div>}
    <div className="canvas-group-actions"><button aria-label="组合选中节点" disabled={s.nodes.filter(n => n.selected).length < 2} onClick={() => { s.group(); notice('选中节点已组合，分组不改变生成依赖'); }}>组合</button><button aria-label="解组选中节点" disabled={!s.nodes.some(n => n.selected && n.data.groupId)} onClick={s.ungroup}>解组</button><button aria-label="选择同组节点" disabled={!s.nodes.some(n => n.selected && n.data.groupId)} onClick={() => { const groups = new Set(s.nodes.filter(n => n.selected).map(n => n.data.groupId).filter(Boolean)); s.replace(s.nodes.map(n => ({ ...n, selected: groups.has(n.data.groupId) })), s.edges, false); }}>选中同组</button></div>
    <div className="canvas-hint">{overview ? `概览模式 · 放大至 ${previewThreshold}% 查看内容` : s.nodes.filter(n => n.selected).length > 1 ? `已选 ${s.nodes.filter(n => n.selected).length} 个节点 · 拖动节点顶部一起移动` : '空白处拖动框选 · Ctrl/Shift 点选多选'} <span>·</span> 空格 + 拖动平移</div>
  </div></InputPortPickerProvider>;
}
