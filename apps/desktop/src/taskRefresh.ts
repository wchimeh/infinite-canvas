import type { Asset, StudioNode, Task } from './types';

type RefreshState = { nodes: StudioNode[]; tasks: Task[]; assets: Asset[] };
const same = (a: unknown, b: unknown) => a === b || JSON.stringify(a) === JSON.stringify(b);

function reuseList<T extends { id: string }>(previous: T[], incoming: T[]): T[] {
  const byId = new Map(previous.map(item => [item.id, item]));
  const next = incoming.map(item => {
    const old = byId.get(item.id);
    return old && same(old, item) ? old : item;
  });
  return next.length === previous.length && next.every((item, index) => item === previous[index]) ? previous : next;
}

export function mergeTaskRefresh<T extends RefreshState>(state: T, incomingTasks: Task[], incomingAssets: Asset[]): T {
  const tasks = reuseList(state.tasks, incomingTasks);
  const assets = reuseList(state.assets, incomingAssets);
  const latest = new Map<string, Task>();
  for (const task of tasks) {
    const old = latest.get(task.node_id);
    if (!old || task.created_at > old.created_at) latest.set(task.node_id, task);
  }
  let changed = false;
  const nodes = state.nodes.map(node => {
    const task = latest.get(node.id);
    if (!task || task.created_at < Number(node.data.modifiedAt || 0) || !same(task.snapshot.config, node.data.config)) return node;
    if (task.status === node.data.status && task.error === node.data.error && same(task.output, node.data.output)) return node;
    changed = true;
    return { ...node, data: { ...node.data, status: task.status, error: task.error, output: task.output } };
  });
  if (!changed && tasks === state.tasks && assets === state.assets) return state;
  return { ...state, tasks, assets, nodes: changed ? nodes : state.nodes };
}
