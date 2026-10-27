import type { Asset, Definition, StudioEdge, StudioNode, Task } from './types';

export type InputCandidate = {
  source: string; sourceHandle: string; type: string; title: string;
  connected: boolean; asset?: Asset; summary?: string;
};

export function inputCandidates(targetId: string, targetHandle: string, nodes: StudioNode[], edges: StudioEdge[], definitions: Record<string, Definition>, tasks: Task[], assets: Asset[]): InputCandidate[] {
  const target = nodes.find(node => node.id === targetId);
  const type = target && definitions[target.data.kind]?.inputs[targetHandle];
  if (!type) return [];
  const downstream = new Map<string, string[]>();
  for (const edge of edges) {
    if (edge.data?.kind === 'sequence') continue;
    const children = downstream.get(edge.source) || [];
    children.push(edge.target);
    downstream.set(edge.source, children);
  }
  const excluded = new Set<string>(), pending = [targetId];
  while (pending.length) {
    const id = pending.pop()!;
    if (excluded.has(id)) continue;
    excluded.add(id);
    pending.push(...downstream.get(id) || []);
  }
  const latest = new Map<string, Task>();
  for (const task of tasks) if (!latest.has(task.node_id) || task.created_at > latest.get(task.node_id)!.created_at) latest.set(task.node_id, task);
  const assetMap = new Map(assets.map(asset => [asset.id, asset]));
  const incoming = edges.filter(edge => edge.target === targetId && edge.targetHandle === targetHandle && edge.data?.kind !== 'sequence');
  const candidates: InputCandidate[] = [];
  for (const node of nodes) {
    if (excluded.has(node.id)) continue;
    const task = latest.get(node.id);
    const output = node.data.status !== 'dirty' && task?.status === 'completed' ? task.output : undefined;
    const ids = node.data.config.assetId ? [node.data.config.assetId] : output?.assets || [];
    const asset = ids.map(id => assetMap.get(id)).find(asset => asset?.mime.startsWith(type + '/'));
    const summary = type === 'text' ? node.data.config.editedResult?.text ?? output?.text ?? node.data.config.prompt : undefined;
    for (const [sourceHandle, outputType] of Object.entries(definitions[node.data.kind]?.outputs || {})) {
      if (outputType !== type) continue;
      candidates.push({ source: node.id, sourceHandle, type, title: node.data.title,
        connected: incoming.some(edge => edge.source === node.id && edge.sourceHandle === sourceHandle),
        asset, summary: summary?.slice(0, 180) });
    }
  }
  return candidates;
}
