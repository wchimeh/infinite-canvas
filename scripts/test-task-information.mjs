import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';

const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const ts = require('typescript');
const source = await readFile(new URL('../apps/desktop/src/taskInformation.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } });
const { taskInformation } = await import('data:text/javascript;base64,' + Buffer.from(outputText).toString('base64'));
const info = (status, extra = {}) => taskInformation({ status, output: {}, reused: false, ...extra });

for (const external_id of [undefined, 'remote-task']) {
  assert.match(info('completed', { external_id }), /任务已完成/);
  assert.doesNotMatch(info('completed', { external_id }), /等待|查询/);
}
assert.match(info('completed', { output: { text: 'result' } }), /文本结果/);
assert.match(info('completed', { output: { assets: ['a', 'b'] } }), /2 个素材结果/);
assert.match(info('completed', { reused: true }), /已复用缓存结果/);
for (const reused of [true, false]) {
  assert.match(info('completed', { snapshot: { kind: 'story.prompt' }, reused, output: { text: 'story' } }), /未调用大模型/);
}
assert.doesNotMatch(info('completed', { snapshot: { kind: 'script.expand' }, output: { text: 'generated' } }), /未调用大模型/);
assert.equal(info('queued'), '等待本地调度');
assert.match(info('queued', { external_id: 'remote' }), /已提交云端/);
assert.match(info('running'), /任务执行中/);
assert.match(info('running', { external_id: 'remote' }), /云端任务处理中/);
for (const state of ['blocked', 'failed', 'cancel_requested', 'cancelled', 'unknown']) {
  assert.doesNotMatch(info(state), /等待本地调度/);
  assert.equal(info(state, { error: 'specific error' }), 'specific error');
}
assert.match(info('cancelled'), /已取消/);
assert.match(info('blocked'), /上游/);
console.log('PASS: completed results, cache, queued/running, errors and terminal states');
