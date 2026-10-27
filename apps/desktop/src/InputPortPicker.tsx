import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { Handle, Position, useStoreApi } from '@xyflow/react';
import { Search, X } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';
import { useStudio } from './store';
import { inputCandidates } from './inputCandidates';
import { InputCandidateList } from './InputCandidateList';

type Port = { nodeId: string; handle: string; label: string; type: string; anchor: HTMLElement; keyboard?: boolean };
type PickerControls = { enter: (port: Port) => void; leave: () => void; keep: () => void; close: () => void };
const PickerContext = createContext<PickerControls | null>(null);
const typeNames: Record<string, string> = { image: '图片', audio: '音频', video: '视频', text: '文本', shots: '分镜' };

export function InputPortPickerProvider({ children }: { children: ReactNode }) {
  const [port, setPort] = useState<Port | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const flow = useStoreApi();
  const keep = useCallback(() => { clearTimeout(timer.current); }, []);
  const close = useCallback(() => { keep(); setPort(null); }, [keep]);
  const controls = useMemo<PickerControls>(() => ({ keep, close,
    enter: next => {
      keep();
      if (flow.getState().connection.inProgress) return;
      if (next.keyboard) setPort(next);
      else timer.current = setTimeout(() => { if (!flow.getState().connection.inProgress) setPort(next); }, 250);
    },
    leave: () => { keep(); timer.current = setTimeout(() => setPort(null), 200); },
  }), [keep, close, flow]);
  useEffect(() => flow.subscribe((state, previous) => {
    if (state.transform !== previous.transform || state.connection.inProgress && !previous.connection.inProgress) close();
  }), [flow, close]);
  useEffect(() => keep, [keep]);
  return <PickerContext.Provider value={controls}>{children}{port && <PickerPopover key={`${port.nodeId}:${port.handle}`} port={port} controls={controls}/>}</PickerContext.Provider>;
}

export function InputPort({ nodeId, name, type, label }: { nodeId: string; name: string; type: string; label: string }) {
  const picker = useContext(PickerContext)!;
  return <Handle type="target" position={Position.Left} id={name} tabIndex={0} role="button" aria-label={`选择${label}输入`} aria-haspopup="dialog"
    onPointerEnter={event => { if (!event.buttons) picker.enter({ nodeId, handle: name, type, label, anchor: event.currentTarget }); }}
    onPointerLeave={picker.leave} onPointerDown={picker.close}
    onKeyDown={event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault(); event.stopPropagation();
        picker.enter({ nodeId, handle: name, type, label, anchor: event.currentTarget, keyboard: true });
      }
    }}/>;
}

function PickerPopover({ port, controls }: { port: Port; controls: PickerControls }) {
  const state = useStudio(useShallow(s => ({ nodes: s.nodes, edges: s.edges, definitions: s.definitions, tasks: s.tasks, assets: s.assets })));
  const candidates = useMemo(() => inputCandidates(port.nodeId, port.handle, state.nodes, state.edges, state.definitions, state.tasks, state.assets), [port, state]);
  const [query, setQuery] = useState(''), [error, setError] = useState('');
  const [position, setPosition] = useState({ left: 0, top: 0 });
  const panel = useRef<HTMLDivElement>(null), search = useRef<HTMLInputElement>(null);
  const visible = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    return needle ? candidates.filter(candidate => `${candidate.title} ${candidate.asset?.name || ''} ${candidate.summary || ''}`.toLocaleLowerCase().includes(needle)) : candidates;
  }, [candidates, query]);
  const typeName = typeNames[port.type] || port.type;
  const occupied = state.edges.some(edge => edge.target === port.nodeId && edge.targetHandle === port.handle && edge.data?.kind !== 'sequence');

  useLayoutEffect(() => {
    const rect = port.anchor.getBoundingClientRect(), box = panel.current!.getBoundingClientRect();
    const preferred = rect.left - box.width - 12;
    const left = preferred >= 8 ? preferred : rect.right + 12;
    setPosition({ left: Math.max(8, Math.min(left, window.innerWidth - box.width - 8)), top: Math.max(8, Math.min(rect.top - 16, window.innerHeight - box.height - 8)) });
  }, [port, visible.length, error]);
  useEffect(() => {
    if (port.keyboard) search.current?.focus();
    const outside = (event: Event) => {
      const target = event.target as Node;
      if (!panel.current?.contains(target) && !port.anchor.contains(target)) controls.close();
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); controls.close(); if (port.keyboard) port.anchor.focus(); }
    };
    document.addEventListener('pointerdown', outside, true);
    document.addEventListener('keydown', escape, true);
    window.addEventListener('resize', controls.close);
    // Scrolling the candidate list is allowed; scrolling the page invalidates the anchor.
    document.addEventListener('scroll', outside, true);
    return () => {
      document.removeEventListener('pointerdown', outside, true);
      document.removeEventListener('keydown', escape, true);
      window.removeEventListener('resize', controls.close);
      document.removeEventListener('scroll', outside, true);
    };
  }, [port, controls]);
  useEffect(() => {
    if (!state.nodes.some(node => node.id === port.nodeId) || !port.anchor.isConnected) controls.close();
  }, [state.nodes, port, controls]);

  return createPortal(<div ref={panel} className="input-port-picker nodrag nopan nowheel" role="dialog" aria-label={`选择${port.label}来源`} style={position}
    onPointerEnter={controls.keep} onPointerLeave={() => { if (!panel.current?.contains(document.activeElement)) controls.leave(); }}
    onFocus={controls.keep} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget) && !event.currentTarget.matches(':hover')) controls.leave(); }}
    onPointerDown={event => event.stopPropagation()} onClick={event => event.stopPropagation()} onWheel={event => event.stopPropagation()} onKeyDown={event => event.stopPropagation()}>
    <header><div><strong>选择{port.label}</strong><small>画布上的{typeName} · {candidates.length} 个来源</small></div><button aria-label="关闭输入选择" onClick={controls.close}><X size={16}/></button></header>
    <label className="input-picker-search"><Search size={15}/><input ref={search} aria-label="搜索输入来源" placeholder="搜索节点或素材名称" value={query} onChange={event => setQuery(event.target.value)}/></label>
    <InputCandidateList key={query} candidates={visible} typeName={typeName}
      emptyText={query ? '没有匹配的来源，试试其他名称。' : `画布上暂无可连接的${typeName}来源。添加对应节点后即可选择。`}
      onSelect={candidate => {
          const result = useStudio.getState().connect({ id: crypto.randomUUID(), source: candidate.source, sourceHandle: candidate.sourceHandle, target: port.nodeId, targetHandle: port.handle, data: { kind: 'data' } });
          if (result) setError(result); else { controls.close(); if (port.keyboard) port.anchor.focus(); }
      }}/>
    {error && <p className="input-picker-error" role="alert">{error}</p>}
    <footer>{occupied ? '选择其他来源将替换此输入点的连线' : '点击来源自动连线，也可直接拖动连接点'}</footer>
  </div>, document.body);
}
