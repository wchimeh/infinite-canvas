import { create } from 'zustand';
import type { Viewport } from '@xyflow/react';
import type { Asset, CanvasDoc, Config, Definition, StudioEdge, StudioNode, Task } from './types';

type Snapshot = { nodes: StudioNode[]; edges: StudioEdge[] };
type State = Snapshot & {
  definitions: Record<string, Definition>; assets: Asset[]; tasks: Task[];
  viewport: Viewport; version: number; edits: number; savedEdits: number;
  past: Snapshot[]; future: Snapshot[];
  focusRequest: { nodeId: string } | null;
  insertionPosition: { x: number; y: number } | null;
  load: (doc: CanvasDoc) => void;
  checkpoint: () => void;
  replace: (nodes: StudioNode[], edges: StudioEdge[], edited?: boolean) => void;
  add: (kind: string, position?: { x: number; y: number }, config?: Config, title?: string) => string;
  patch: (id: string, data: Partial<StudioNode['data']>) => void;
  connect: (edge: StudioEdge) => string | null;
  duplicate: () => void; remove: () => void; undo: () => void; redo: () => void;
  group: (title?: string) => void; ungroup: () => void;
};

function dirty(nodes: StudioNode[], edges: StudioEdge[], ids: string[]) {
  const affected = new Set(ids);
  let added = true;
  while (added) {
    added = false;
    for (const e of edges) if (e.data?.kind !== 'sequence' && affected.has(e.source) && !affected.has(e.target)) {
      affected.add(e.target); added = true;
    }
  }
  return nodes.map(n => affected.has(n.id) ? { ...n, data: { ...n.data, status: 'dirty', error: undefined, modifiedAt: Date.now() / 1000 } } : n);
}

function syncShotDuration(nodes: StudioNode[], edges: StudioEdge[]) {
  let next = nodes;
  for (let pass = 0; pass < nodes.length; pass++) {
    let changed = false;
    for (const edge of edges) {
      if (edge.data?.kind === 'sequence' || edge.targetHandle !== 'text') continue;
      const source = next.find(node => node.id === edge.source);
      const target = next.find(node => node.id === edge.target);
      if (!source || !target || !['prompt.video_expand', 'video.image_to_video'].includes(target.data.kind)) continue;
      const seconds = source.data.kind === 'shots.select' ? (source.data.config.selectedShot?.durationMs || 0) / 1000
        : source.data.kind === 'prompt.video_expand' ? source.data.config.seconds : undefined;
      if (seconds === undefined || seconds < 4 || seconds > 15 || target.data.config.seconds === seconds) continue;
      changed = true;
      next = next.map(node => node.id === target.id ? { ...node, data: { ...node.data, config: { ...node.data.config, seconds } } } : node);
    }
    if (!changed) break;
  }
  return next;
}

export const useStudio = create<State>((set, get) => ({
  nodes: [], edges: [], definitions: {}, assets: [], tasks: [], viewport: { x: 0, y: 0, zoom: 1 },
  version: 1, edits: 0, savedEdits: 0, past: [], future: [], focusRequest: null, insertionPosition: null,
  load: doc => set({ ...doc, edits: 0, savedEdits: 0, past: [], future: [], tasks: [], focusRequest: null, insertionPosition: null }),
  checkpoint: () => { const s = get(); set({ past: [...s.past.slice(-49), { nodes: structuredClone(s.nodes), edges: structuredClone(s.edges) }], future: [] }); },
  replace: (nodes, edges, edited = true) => set(s => ({ nodes, edges, edits: s.edits + Number(edited) })),
  add: (kind, position, config = {}, title) => {
    const s = get(); s.checkpoint(); const id = crypto.randomUUID();
    set({ nodes: [...s.nodes.map(n => ({ ...n, selected: false })), {
      id, type: 'studio', position: { ...(position || s.insertionPosition || { x: 100 + s.nodes.length % 3 * 330, y: 100 + Math.floor(s.nodes.length / 3) * 280 }) }, selected: true,
      data: { kind, title: title || s.definitions[kind]?.displayName || kind, config, status: 'idle' },
    }], edits: s.edits + 1 }); return id;
  },
  patch: (id, data) => {
    const s = get(); s.checkpoint();
    const nodes = s.nodes.map(n => n.id === id ? { ...n, data: { ...n.data, ...data } } : n);
    set({ nodes: syncShotDuration(dirty(nodes, s.edges, [id]), s.edges), edits: s.edits + 1 });
  },
  connect: edge => {
    const s = get(); const source = s.nodes.find(n => n.id === edge.source), target = s.nodes.find(n => n.id === edge.target);
    if (!source || !target) return '连接节点不存在';
    const out = s.definitions[source.data.kind]?.outputs[edge.sourceHandle || ''];
    const input = s.definitions[target.data.kind]?.inputs[edge.targetHandle || ''];
    if (!out || out !== input) return '端口类型不匹配，请连接相同类型的素材';
    if (s.edges.some(e => e.source === edge.source && e.target === edge.target && e.sourceHandle === edge.sourceHandle && e.targetHandle === edge.targetHandle)) return '这条连接已存在';
    const retained = s.edges.filter(e => e.data?.kind === 'sequence' || e.target !== edge.target || e.targetHandle !== edge.targetHandle);
    const seen = new Set<string>(); const stack = [edge.target];
    while (stack.length) { const id = stack.pop()!; if (id === edge.source) return '此连接会产生循环依赖'; if (seen.has(id)) continue; seen.add(id); stack.push(...retained.filter(e => e.source === id && e.data?.kind !== 'sequence').map(e => e.target)); }
    s.checkpoint(); const edges = [...retained, edge]; set({ edges, nodes: syncShotDuration(dirty(s.nodes, edges, [edge.target]), edges), edits: s.edits + 1 }); return null;
  },
  duplicate: () => {
    const s = get(); const selected = s.nodes.filter(n => n.selected); if (!selected.length) return;
    s.checkpoint(); const ids = new Map(selected.map(n => [n.id, crypto.randomUUID()]));
    const copies = selected.map(n => ({ ...structuredClone(n), id: ids.get(n.id)!, position: { x: n.position.x + 45, y: n.position.y + 45 }, data: { ...n.data, title: n.data.title + ' 副本', status: 'idle', output: undefined } }));
    const edges = s.edges.filter(e => ids.has(e.source) && ids.has(e.target)).map(e => ({ ...e, id: crypto.randomUUID(), source: ids.get(e.source)!, target: ids.get(e.target)! }));
    set({ nodes: [...s.nodes.map(n => ({ ...n, selected: false })), ...copies], edges: [...s.edges, ...edges], edits: s.edits + 1 });
  },
  group: (title = '镜头组') => {
    const s = get(), selected = s.nodes.filter(n => n.selected);
    if (selected.length < 2) return;
    s.checkpoint(); const groupId = crypto.randomUUID();
    set({ nodes: s.nodes.map(n => n.selected ? { ...n, data: { ...n.data, groupId, groupTitle: title } } : n), edits: s.edits + 1 });
  },
  ungroup: () => {
    const s = get(), groups = new Set(s.nodes.filter(n => n.selected).map(n => n.data.groupId).filter(Boolean));
    if (!groups.size) return;
    s.checkpoint();
    set({ nodes: s.nodes.map(n => groups.has(n.data.groupId) ? { ...n, data: { ...n.data, groupId: undefined, groupTitle: undefined } } : n), edits: s.edits + 1 });
  },
  remove: () => {
    const s = get(); s.checkpoint(); const ids = new Set(s.nodes.filter(n => n.selected).map(n => n.id));
    const affected = s.edges.filter(e => ids.has(e.source) || e.selected).map(e => e.target);
    const edges = s.edges.filter(e => !ids.has(e.source) && !ids.has(e.target) && !e.selected);
    set({ nodes: dirty(s.nodes.filter(n => !ids.has(n.id)), s.edges, affected), edges, edits: s.edits + 1 });
  },
  undo: () => { const s = get(), previous = s.past.at(-1); if (previous) set({ ...previous, past: s.past.slice(0, -1), future: [{ nodes: s.nodes, edges: s.edges }, ...s.future], edits: s.edits + 1 }); },
  redo: () => { const s = get(), next = s.future[0]; if (next) set({ ...next, future: s.future.slice(1), past: [...s.past, { nodes: s.nodes, edges: s.edges }], edits: s.edits + 1 }); },
}));
