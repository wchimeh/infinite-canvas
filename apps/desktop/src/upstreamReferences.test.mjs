import assert from 'node:assert/strict';
import test from 'node:test';
import { connectUpstreamReferences } from './upstreamReferences.ts';

const defs = {
  image: { inputs: {}, outputs: { image: 'image' } },
  'asset.image': { inputs: {}, outputs: { image: 'image' } },
  expand: { inputs: { text: 'text', image: 'image', image2: 'image' }, outputs: { text: 'text' } },
  video: { inputs: { text: 'text', image: 'image', image2: 'image', image3: 'image', image4: 'image', audio: 'audio' }, outputs: { video: 'video' } },
};
const node = (id, kind, config = {}) => ({ id, position: { x: 0, y: 0 }, data: { kind, config } });
const edge = (source, target, targetHandle, sourceHandle = 'image') => ({ id: `${source}-${target}-${targetHandle}`, source, target, sourceHandle, targetHandle, data: { kind: 'data' } });
function fixture() {
  return { nodes: [node('a', 'image'), node('b', 'image'), node('up', 'expand', { referenceIds: ['picked', 'sound'] }), node('target', 'video', { referenceIds: ['old', 'sound'] })],
    edges: [edge('b', 'up', 'image2'), edge('a', 'up', 'image'), edge('up', 'target', 'text', 'text'), edge('sound', 'target', 'audio', 'audio'), edge('b', 'target', 'image')],
    assets: [{ id: 'picked', name: 'Picked', mime: 'image/png' }, { id: 'old', mime: 'image/png' }, { id: 'sound', mime: 'audio/wav' }] };
}
test('按上游端口及勾选顺序自动连线，保留音频，重复点击复用素材节点', () => {
  const f = fixture(); let i = 0; const id = () => `new-${i++}`;
  const result = connectUpstreamReferences('target', f.nodes, f.edges, f.assets, defs, id);
  assert.equal(result.count, 3);
  const added = result.nodes.find(n => n.data.kind === 'asset.image');
  assert.equal(added.data.config.assetId, 'picked');
  const images = result.edges.filter(e => e.target === 'target' && e.targetHandle.startsWith('image'));
  assert.deepEqual(images.map(e => [e.source, e.targetHandle]), [['a', 'image'], ['b', 'image2'], [added.id, 'image3']]);
  assert.ok(result.edges.some(e => e.targetHandle === 'audio'));
  assert.deepEqual(result.nodes.find(n => n.id === 'target').data.config.referenceIds, ['sound']);
  assert.equal(connectUpstreamReferences('target', result.nodes, result.edges, f.assets, defs, id).nodes.length, result.nodes.length);
  assert.equal(f.nodes.length, 4);
});
test('端口不足或素材缺失时不修改原图', () => {
  const f = fixture(), before = structuredClone(f);
  assert.throws(() => connectUpstreamReferences('target', f.nodes, f.edges, f.assets, { ...defs, video: { inputs: { text: 'text', image: 'image' } } }, () => 'id'), /无法全部连接/);
  assert.throws(() => connectUpstreamReferences('target', f.nodes, f.edges, [], defs, () => 'id'), /缺失/);
  assert.deepEqual(f, before);
});
test('无上游和多个文本上游明确拒绝', () => {
  const f = fixture();
  assert.throws(() => connectUpstreamReferences('target', f.nodes, [], f.assets, defs, () => 'id'), /先连接/);
  assert.throws(() => connectUpstreamReferences('target', f.nodes, [...f.edges, edge('another', 'target', 'text', 'text')], f.assets, defs, () => 'id'), /多个上游/);
});
