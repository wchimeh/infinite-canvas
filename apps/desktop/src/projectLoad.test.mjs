import assert from 'node:assert/strict';
import test from 'node:test';

import { createProjectLoadGate } from './projectLoad.ts';

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

test('操作快照不推进世代，A→B→A 后旧操作仍然失效', () => {
  const gate = createProjectLoadGate();
  const current = gate.begin();
  const operation = gate.snapshot();
  assert.equal(operation, current);
  assert.equal(gate.snapshot(), operation);
  assert.equal(gate.isLatest(operation), true);
  gate.begin();
  gate.begin();
  assert.equal(gate.isLatest(operation), false);
  assert.equal(gate.isLatest(gate.snapshot()), true);
});

test('逆序响应只能提交最新项目，切换开始即退出可编辑态', async () => {
  const gate = createProjectLoadGate();
  const responseA = deferred();
  const responseB = deferred();
  let currentProject = 'original';

  const load = async (id, response) => {
    const request = gate.begin();
    currentProject = undefined;
    const value = await response.promise;
    if (gate.isLatest(request)) currentProject = value;
  };

  const loadingA = load('A', responseA);
  assert.equal(currentProject, undefined);
  const loadingB = load('B', responseB);
  responseB.resolve('B');
  await loadingB;
  assert.equal(currentProject, 'B');
  responseA.resolve('A');
  await loadingA;
  assert.equal(currentProject, 'B');
});
