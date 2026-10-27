import type { Asset, Definition, StudioEdge, StudioNode } from './types';

export function connectUpstreamReferences(targetId: string, nodes: StudioNode[], edges: StudioEdge[], assets: Asset[], definitions: Record<string, Definition>, id: () => string) {
  const target = nodes.find(n => n.id === targetId);
  if (!target) throw new Error('当前节点不存在');
  const inputs = definitions[target.data.kind]?.inputs || {};
  const ports = Object.keys(inputs).filter(port => inputs[port] === 'image').sort((a, b) => Number(a.slice(5) || 1) - Number(b.slice(5) || 1));
  const incoming = edges.filter(e => e.target === targetId && e.data?.kind !== 'sequence');
  const textSources = incoming.filter(e => inputs[e.targetHandle || ''] === 'text');
  const sources = [...new Set((textSources.length ? textSources : incoming.filter(e => inputs[e.targetHandle || ''] === 'image')).map(e => e.source))];
  if (sources.length !== 1) throw new Error(sources.length ? '有多个上游节点，请保留一个明确的文本上游后再连接参考图' : '请先连接一个上游节点');
  const upstream = nodes.find(n => n.id === sources[0]);
  if (!upstream) throw new Error('上游节点不存在');
  const upstreamInputs = definitions[upstream.data.kind]?.inputs || {};
  const references = edges.filter(e => e.target === upstream.id && e.data?.kind !== 'sequence' && upstreamInputs[e.targetHandle || ''] === 'image')
    .sort((a, b) => Number(a.targetHandle?.slice(5) || 1) - Number(b.targetHandle?.slice(5) || 1))
    .map(e => ({ source: e.source, sourceHandle: e.sourceHandle || 'image' }));
  const images: Asset[] = [];
  for (const aid of upstream.data.config.referenceIds || []) {
    const asset = assets.find(a => a.id === aid);
    if (!asset) throw new Error('上游有参考素材已缺失，请先重新绑定');
    if (asset.mime.startsWith('image/')) images.push(asset);
  }
  const count = references.length + images.length;
  if (!count) throw new Error('上游节点没有使用参考图');
  if (count > ports.length) throw new Error(`上游有 ${count} 张参考图，当前节点只有 ${ports.length} 个图片输入口，无法全部连接`);
  for (const reference of references) {
    const source = nodes.find(n => n.id === reference.source);
    if (!source || source.id === targetId || definitions[source.data.kind]?.outputs[reference.sourceHandle] !== 'image') throw new Error('上游图片连线无效，请先检查连接');
  }
  const nextNodes = [...nodes];
  for (const asset of images) {
    let source = nextNodes.find(n => n.data.kind === 'asset.image' && n.data.config.assetId === asset.id);
    if (!source) {
      const x = target.position.x - 340;
      let y = target.position.y;
      while (nextNodes.some(n => x < n.position.x + (n.measured?.width || 280) + 20 && x + 300 > n.position.x && y < n.position.y + (n.measured?.height || 300) + 20 && y + 320 > n.position.y)) y += 340;
      source = { id: id(), type: 'studio', position: { x, y }, data: { kind: 'asset.image', title: asset.name, config: { assetId: asset.id }, status: 'idle' } };
      nextNodes.push(source);
    }
    references.push({ source: source.id, sourceHandle: 'image' });
  }
  const nextEdges = edges.filter(e => e.target !== targetId || e.data?.kind === 'sequence' || inputs[e.targetHandle || ''] !== 'image');
  references.forEach((reference, index) => nextEdges.push({ id: id(), ...reference, target: targetId, targetHandle: ports[index], data: { kind: 'data' } }));
  // Keep audio/video selections; images now arrive exclusively through visible wires.
  const referenceIds = (target.data.config.referenceIds || []).filter(aid => !assets.find(a => a.id === aid)?.mime.startsWith('image/'));
  return { nodes: nextNodes.map(n => n.id === targetId ? { ...n, data: { ...n.data, config: { ...n.data.config, referenceIds } } } : n), edges: nextEdges, count };
}
