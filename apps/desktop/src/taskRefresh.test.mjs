import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { transformWithEsbuild } from 'vite';

const source = await readFile(new URL('./taskRefresh.ts', import.meta.url), 'utf8');
const { code } = await transformWithEsbuild(source, 'taskRefresh.ts', { loader: 'ts', format: 'esm' });
const { mergeTaskRefresh } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const copy = value => structuredClone(value);
function fixture(count = 2) {
  const nodes = Array.from({ length: count }, (_, i) => ({ id: `n${i}`, data: { config: {}, status: 'completed', output: { text: `${i}` } } }));
  const tasks = nodes.map(n => ({ id: `t${n.id}`, node_id: n.id, created_at: 10, snapshot: { config: {} }, status: 'completed', output: n.data.output }));
  return { nodes, tasks, assets: [{ id: 'a', name: 'original' }] };
}
test('重复响应复用整个状态，不触发订阅更新', () => {
  const state = fixture();
  assert.equal(mergeTaskRefresh(state, copy(state.tasks), copy(state.assets)), state);
});
test('只替换结果变化的节点，素材改名和删除正常同步', () => {
  const state = fixture(); const tasks = copy(state.tasks);
  tasks[0].output.text = 'new';
  const next = mergeTaskRefresh(state, tasks, [{ id: 'a', name: 'renamed' }]);
  assert.notEqual(next.nodes[0], state.nodes[0]);
  assert.equal(next.nodes[1], state.nodes[1]);
  assert.equal(next.tasks[1], state.tasks[1]);
  assert.equal(next.assets[0].name, 'renamed');
  assert.deepEqual(mergeTaskRefresh(next, tasks, []).assets, []);
});
test('旧任务和不匹配的配置不能覆盖新编辑', () => {
  const state = fixture(); state.nodes[0].data.modifiedAt = 11; state.nodes[0].data.status = 'dirty';
  state.nodes[1].data.config = { prompt: 'new' };
  assert.equal(mergeTaskRefresh(state, copy(state.tasks), copy(state.assets)), state);
});
test('多次运行使用最新任务，不依赖服务端排序', () => {
  const state = fixture(); const newer = { ...state.tasks[0], id: 'new', created_at: 12, output: { text: 'latest' } };
  assert.equal(mergeTaskRefresh(state, [...state.tasks, newer], state.assets).nodes[0].data.output.text, 'latest');
});
test('五千节点中仅一个任务变化时，其余节点全部复用', () => {
  const state = fixture(5000); const tasks = copy(state.tasks); tasks[4999].status = 'running';
  const next = mergeTaskRefresh(state, tasks, state.assets);
  assert.equal(next.nodes.filter((n, i) => n !== state.nodes[i]).length, 1);
});
