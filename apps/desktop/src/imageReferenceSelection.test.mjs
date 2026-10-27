import assert from 'node:assert/strict';
import test from 'node:test';
import { connectedImageIds, selectImageReference } from './imageReferenceSelection.ts';
const definitions = { target: { inputs: { image: 'image', image2: 'image', image3: 'image' } } };
const assets = ['a', 'b', 'c', 'd'].map(id => ({ id, name: id, mime: 'image/png' })).concat([{ id: 'audio', mime: 'audio/wav' }]);
const target = { id: 't', position: { x: 0, y: 0 }, data: { kind: 'target', config: { referenceIds: ['audio'] } } };
let sequence = 0;
const apply = (plan, aid, checked, defs = definitions) => selectImageReference('t', aid, checked, plan.nodes, plan.edges, assets, defs, [], () => `new-${sequence++}`);
test('勾选创建连线、取消移线、素材节点复用且音频保留', () => {
  let plan = apply({ nodes: [target], edges: [] }, 'a', true);
  plan = apply(plan, 'b', true);
  assert.equal(plan.nodes.length, 3); assert.equal(plan.edges.length, 2);
  assert.deepEqual(plan.nodes[0].data.config.referenceIds, ['audio']);
  assert.deepEqual([...connectedImageIds('t', plan.nodes, plan.edges, definitions, [])], ['a', 'b']);
  assert.equal(apply(plan, 'a', true).edges.length, 2);
  plan = apply(plan, 'a', false);
  assert.equal(plan.nodes.length, 3); assert.equal(plan.edges.length, 1);
  assert.equal(plan.edges[0].targetHandle, 'image');
  plan = apply(plan, 'a', true);
  assert.equal(plan.nodes.length, 3);
  assert.deepEqual([...connectedImageIds('t', plan.nodes, plan.edges, definitions, [])], ['b', 'a']);
});
test('旧勾选转换为连线，顺序稳定且无双份输入', () => {
  const old = { ...target, data: { ...target.data, config: { referenceIds: ['b', 'audio', 'a'] } } };
  const plan = apply({ nodes: [old], edges: [] }, 'c', true);
  assert.deepEqual([...connectedImageIds('t', plan.nodes, plan.edges, definitions, [])], ['b', 'a', 'c']);
  assert.deepEqual(plan.nodes[0].data.config.referenceIds, ['audio']);
  const original = structuredClone(plan);
  assert.throws(() => apply(plan, 'd', true), /最多连接/);
  assert.deepEqual(plan, original);
});
test('删除连接后勾选消失，生成输出连线可识别', () => {
  const nodes = [target, { id: 'generated', data: { kind: 'image.generate', config: {} } }];
  const edges = [{ id: 'edge', source: 'generated', target: 't', targetHandle: 'image' }];
  const tasks = [{ node_id: 'generated', created_at: 1, status: 'completed', output: { assets: ['a'] } }];
  assert.deepEqual([...connectedImageIds('t', nodes, edges, definitions, tasks)], ['a']);
  assert.equal(connectedImageIds('t', nodes, [], definitions, tasks).size, 0);
});
