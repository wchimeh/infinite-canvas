import type { Asset, StudioEdge, Task } from './types';

const defaults = { image: 1, audio: 1, video: 1, videoAudio: 1, text: 1 };
type Counts = typeof defaults;
const ports = new WeakMap<StudioEdge[], Map<string, { normal: Counts; character: Counts }>>();
const tasks = new WeakMap<Task[], Map<string, Task>>();
const assets = new WeakMap<Asset[], Map<string, Asset>>();

export function portCounts(edges: StudioEdge[], nodeId: string, character = false): Counts {
  let index = ports.get(edges);
  if (!index) {
    index = new Map();
    for (const edge of edges) {
      if (edge.data?.kind === 'sequence') continue;
      const match = /^(image|audio|video|videoAudio|text)([2-9]|10)?$/.exec(edge.targetHandle || '');
      if (!match) continue;
      const id = edge.target;
      let entry = index.get(id);
      if (!entry) { entry = { normal: { ...defaults }, character: { ...defaults } }; index.set(id, entry); }
      const group = match[1] as keyof Counts;
      const count = Number(match[2] || 1) + 1;
      const limit = group === 'image' ? 9 : group === 'text' ? 10 : 3;
      entry.normal[group] = Math.min(limit, Math.max(entry.normal[group], count));
      entry.character[group] = Math.min(group === 'image' ? 8 : limit, entry.normal[group]);
    }
    ports.set(edges, index);
  }
  return index.get(nodeId)?.[character ? 'character' : 'normal'] || defaults;
}

export function nodeTask(values: Task[], nodeId: string): Task | undefined {
  let index = tasks.get(values);
  if (!index) {
    index = new Map();
    for (const task of values) if (!index.has(task.node_id)) index.set(task.node_id, task);
    tasks.set(values, index);
  }
  return index.get(nodeId);
}

export function indexedAsset(values: Asset[], id?: string): Asset | undefined {
  if (!id) return undefined;
  let index = assets.get(values);
  if (!index) {
    index = new Map();
    for (const asset of values) if (!index.has(asset.id)) index.set(asset.id, asset);
    assets.set(values, index);
  }
  return index.get(id);
}
