import assert from 'node:assert/strict';
import test from 'node:test';
import { portCounts, nodeTask, indexedAsset } from './canvasIndexes.ts';
const edge = (target, targetHandle, kind = 'data') => ({ target, targetHandle, data: { kind } });

test('端口计数保留动态端口规则、类型上限和顺序边排除', () => {
  const edges = [edge('n', 'image7'), edge('n', 'text10'), edge('n', 'audio3'), edge('n', 'video2'), edge('n', 'videoAudio3'), edge('n', 'image9', 'sequence'), edge('other', 'image9')];
  assert.deepEqual(portCounts(edges, 'n', true), { image: 8, audio: 3, video: 3, videoAudio: 3, text: 10 });
  assert.equal(portCounts([edge('n', 'image9')], 'n', true).image, 8);
  assert.equal(portCounts([edge('n', 'image9')], 'n', false).image, 9);
  assert.deepEqual(portCounts([], 'n'), { image: 1, audio: 1, video: 1, videoAudio: 1, text: 1 });
});
test('相同数组复用索引和计数对象，不可变更新后重新计算', () => {
  const edges = [edge('n', 'image')];
  const first = portCounts(edges, 'n');
  assert.strictEqual(portCounts(edges, 'n'), first);
  assert.equal(portCounts([...edges, edge('n', 'image2')], 'n').image, 3);
  assert.equal(first.image, 2);
});
test('任务和素材索引与原 find 顺序一致，数组替换可刷新数据', () => {
  const tasks = [{ node_id: 'n', id: 'latest' }, { node_id: 'n', id: 'older' }];
  const assets = [{ id: 'a', name: 'before' }];
  assert.strictEqual(nodeTask(tasks, 'n'), tasks[0]);
  assert.strictEqual(indexedAsset(assets, 'a'), assets[0]);
  assert.equal(indexedAsset([{ id: 'a', name: 'after' }], 'a').name, 'after');
  assert.equal(nodeTask(tasks, 'absent'), undefined);
  assert.equal(indexedAsset(assets, undefined), undefined);
});
test('高频节点查询不反复读取所有连线', () => {
  let reads = 0;
  const edges = Array.from({ length: 300 }, (_, i) => ({ get target() { reads++; return `n${i % 200}`; }, targetHandle: 'image' }));
  for (let pass = 0; pass < 20; pass++) for (let i = 0; i < 200; i++) portCounts(edges, `n${i}`);
  assert.ok(reads <= 900, `连线属性读取过多：${reads}`);
});
