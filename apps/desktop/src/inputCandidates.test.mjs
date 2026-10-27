import assert from 'node:assert/strict';
import test from 'node:test';
import { inputCandidates } from './inputCandidates.ts';

const types = ['image', 'audio', 'video', 'text', 'shots'];
const definitions = Object.fromEntries(types.map(type => [type, { inputs: { in: type }, outputs: { out: type } }]));
definitions.mixed = { inputs: {}, outputs: { picture: 'image', sound: 'audio' } };
const node = (id, kind, config = {}, status = 'idle') => ({ id, data: { kind, title: id, config, status } });
const edge = (source, target, kind = 'data') => ({ source, target, sourceHandle: 'out', targetHandle: 'in', data: { kind } });
const get = (kind, sources, edges = [], tasks = [], assets = []) => inputCandidates('target', 'in', [node('target', kind), ...sources], edges, definitions, tasks, assets);

test('所有输入类型匹配输出端口，包括自定义类型与屏幕外节点', () => {
  for (const type of types) {
    const candidates = get(type, types.map(t => ({ ...node(t, t), position: { x: 100000, y: 100000 } })));
    assert.deepEqual(candidates.map(c => [c.source, c.sourceHandle, c.type]), [[type, 'out', type]]);
  }
  assert.equal(get('audio', [node('multi', 'mixed')])[0].sourceHandle, 'sound');
});

test('排除自身与多层下游，顺序边不构成数据依赖', () => {
  const nodes = ['first', 'second', 'safe'].map(id => node(id, 'image'));
  const edges = [edge('target', 'first'), edge('first', 'second'), edge('target', 'safe', 'sequence')];
  assert.deepEqual(get('image', nodes, edges).map(c => c.source), ['safe']);
});

test('只标记当前端口的现有连接，不排除连接到其他输入点的来源', () => {
  const candidates = get('image', [node('a', 'image'), node('b', 'image')], [edge('a', 'target'), { ...edge('b', 'target'), targetHandle: 'image2' }]);
  assert.deepEqual(candidates.map(c => c.connected), [true, false]);
});

test('本地素材及最新完成输出按媒体类型提供预览，不展示旧任务或失效结果', () => {
  const assets = [{ id: 'pic', mime: 'image/png', name: '图片' }, { id: 'sound', mime: 'audio/wav', name: '声音' }];
  const tasks = [
    { node_id: 'generated', created_at: 1, status: 'completed', output: { assets: ['sound'] } },
    { node_id: 'generated', created_at: 2, status: 'completed', output: { assets: ['sound', 'pic'] } },
  ];
  assert.equal(get('image', [node('asset', 'image', { assetId: 'pic' })], [], [], assets)[0].asset.id, 'pic');
  assert.equal(get('image', [node('generated', 'image')], [], tasks, assets)[0].asset.id, 'pic');
  assert.equal(get('image', [node('generated', 'image', {}, 'dirty')], [], tasks, assets)[0].asset, undefined);
  assert.equal(get('image', [node('generated', 'image')], [], [...tasks, { node_id: 'generated', created_at: 3, status: 'failed', output: {} }], assets)[0].asset, undefined);
  assert.equal(get('image', [node('missing', 'image', { assetId: 'gone' })], [], [], assets)[0].asset, undefined);
});

test('文本摘要优先使用编辑稿，本地提示词及生成文本可识别', () => {
  assert.equal(get('text', [node('edited', 'text', { editedResult: { text: '编辑内容' } })])[0].summary, '编辑内容');
  assert.equal(get('text', [node('prompt', 'text', { prompt: '本地输入' })])[0].summary, '本地输入');
  const tasks = [{ node_id: 'generated', created_at: 1, status: 'completed', output: { text: '生成内容' } }];
  assert.equal(get('text', [node('generated', 'text')], [], tasks)[0].summary, '生成内容');
});

test('目标或端口不存在返回空列表，筛选不修改画布', () => {
  const nodes = [node('a', 'image')], before = structuredClone(nodes);
  assert.deepEqual(inputCandidates('absent', 'in', nodes, [], definitions, [], []), []);
  assert.deepEqual(inputCandidates('a', 'absent', nodes, [], definitions, [], []), []);
  assert.deepEqual(nodes, before);
});
