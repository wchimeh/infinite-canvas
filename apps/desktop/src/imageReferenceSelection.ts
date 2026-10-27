import type { Asset, Definition, StudioEdge, StudioNode, Task } from './types';

function sourceAssets(sourceId: string, nodes: StudioNode[], tasks: Task[]): string[] {
  const source = nodes.find(n => n.id === sourceId);
  if (!source) return [];
  if (source.data.config.assetId) return [source.data.config.assetId];
  if (source.data.status === 'dirty') return [];
  const task = tasks.filter(t => t.node_id === sourceId).sort((a, b) => b.created_at - a.created_at)[0];
  return task?.status === 'completed' ? task.output.assets || [] : [];
}

export function connectedImageIds(targetId: string, nodes: StudioNode[], edges: StudioEdge[], definitions: Record<string, Definition>, tasks: Task[]) {
  const target = nodes.find(n => n.id === targetId);
  const inputs = target ? definitions[target.data.kind]?.inputs || {} : {};
  return new Set(edges.filter(e => e.target === targetId && e.data?.kind !== 'sequence' && inputs[e.targetHandle || ''] === 'image').flatMap(e => sourceAssets(e.source, nodes, tasks)));
}

export function selectImageReference(targetId: string, assetId: string, checked: boolean, nodes: StudioNode[], edges: StudioEdge[], assets: Asset[], definitions: Record<string, Definition>, tasks: Task[], id: () => string) {
  const target = nodes.find(n => n.id === targetId);
  if (!target || !assets.some(a => a.id === assetId && a.mime.startsWith('image/'))) throw new Error('图片素材不存在，请刷新后重试');
  const inputs = definitions[target.data.kind]?.inputs || {};
  const ports = Object.keys(inputs).filter(p => inputs[p] === 'image').sort((a, b) => Number(a.slice(5) || 1) - Number(b.slice(5) || 1));
  const imageEdges = edges.filter(e => e.target === targetId && e.data?.kind !== 'sequence' && inputs[e.targetHandle || ''] === 'image');
  const retained = imageEdges.filter(e => checked || !sourceAssets(e.source, nodes, tasks).includes(assetId))
    .sort((a, b) => Number(a.targetHandle?.slice(5) || 1) - Number(b.targetHandle?.slice(5) || 1));
  const wired = new Set(retained.flatMap(e => sourceAssets(e.source, nodes, tasks)));
  const legacy = (target.data.config.referenceIds || []).filter(aid => assets.find(a => a.id === aid)?.mime.startsWith('image/') && (checked || aid !== assetId));
  const additions = [...new Set([...legacy, ...(checked ? [assetId] : [])])].filter(aid => !wired.has(aid));
  if (retained.length + additions.length > ports.length) throw new Error(`当前节点最多连接 ${ports.length} 张参考图，请先取消部分图片`);
  const nextNodes = [...nodes];
  for (const aid of additions) {
    const asset = assets.find(a => a.id === aid)!;
    let source = nextNodes.find(n => n.data.kind === 'asset.image' && n.data.config.assetId === aid);
    if (!source) {
      const x = target.position.x - 340; let y = target.position.y;
      while (nextNodes.some(n => x < n.position.x + (n.measured?.width || 280) + 20 && x + 300 > n.position.x && y < n.position.y + (n.measured?.height || 300) + 20 && y + 320 > n.position.y)) y += 340;
      source = { id: id(), type: 'studio', position: { x, y }, data: { kind: 'asset.image', title: asset.name, config: { assetId: aid }, status: 'idle' } };
      nextNodes.push(source);
    }
    retained.push({ id: id(), source: source.id, sourceHandle: 'image', target: targetId, targetHandle: '', data: { kind: 'data' } });
  }
  const imageEdgeIds = new Set(imageEdges.map(e => e.id));
  const nextEdges = [...edges.filter(e => !imageEdgeIds.has(e.id)), ...retained.map((e, index) => ({ ...e, targetHandle: ports[index] }))];
  const referenceIds = (target.data.config.referenceIds || []).filter(aid => !assets.find(a => a.id === aid)?.mime.startsWith('image/'));
  return { nodes: nextNodes.map(n => n.id === targetId ? { ...n, data: { ...n.data, config: { ...n.data.config, referenceIds } } } : n), edges: nextEdges };
}
