import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { transformWithEsbuild } from 'vite';

const source = await readFile(new URL('./api.ts', import.meta.url), 'utf8');
const transformed = await transformWithEsbuild(source, 'api.ts', { loader: 'ts', format: 'esm' });
const moduleUrl = `data:text/javascript;base64,${Buffer.from(transformed.code).toString('base64')}`;
const { connectSession, api, ApiError } = await import(moduleUrl);

function installBrowserState({ responseOk }) {
  const locationState = {
    hash: '#token=one-time-secret',
    pathname: '/canvas',
    search: '?project=demo',
  };
  const replacements = [];
  const fragmentsSeenByFetch = [];

  globalThis.location = locationState;
  globalThis.history = {
    replaceState(_state, _unused, url) {
      replacements.push(url);
      locationState.hash = '';
    },
  };
  globalThis.fetch = async () => {
    fragmentsSeenByFetch.push(locationState.hash);
    return {
      ok: responseOk,
      status: responseOk ? 200 : 401,
      json: async () => responseOk ? {} : { message: '会话已失效' },
    };
  };

  return { locationState, replacements, fragmentsSeenByFetch };
}

test('会话成功时，请求发出前已清除启动 token', async () => {
  const state = installBrowserState({ responseOk: true });

  await connectSession();

  assert.deepEqual(state.fragmentsSeenByFetch, ['']);
  assert.deepEqual(state.replacements, ['/canvas?project=demo']);
  assert.equal(state.locationState.hash, '');
});

test('会话失败时，地址栏和当前历史项不残留启动 token', async () => {
  const state = installBrowserState({ responseOk: false });

  await assert.rejects(connectSession(), /会话已失效/);

  assert.deepEqual(state.fragmentsSeenByFetch, ['']);
  assert.deepEqual(state.replacements, ['/canvas?project=demo']);
  assert.equal(state.locationState.hash, '');
});

test('查询超时包含读取响应体，且不会重发请求', async () => {
  let calls = 0;
  globalThis.fetch = async (_url, { signal }) => {
    calls++;
    return { ok: true, json: () => new Promise((_, reject) => signal.addEventListener('abort', () => reject(signal.reason))) };
  };
  await assert.rejects(api('/tasks', { timeoutMs: 20 }), error => error instanceof ApiError && error.retryable && /超时/.test(error.message));
  assert.equal(calls, 1);
});

test('调用方取消传递给请求，不误报超时', async () => {
  globalThis.fetch = (_url, { signal }) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(signal.reason)));
  const controller = new AbortController();
  const pending = api('/tasks', { signal: controller.signal });
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
});

test('服务临时故障允许重试，冲突禁止重试，POST 本身只发送一次', async () => {
  for (const [status, retryable] of [[503, true], [409, false], [401, false]]) {
    let calls = 0;
    globalThis.fetch = async () => { calls++; return { ok: false, status, json: async () => ({ message: 'failure' }) }; };
    await assert.rejects(api('/runs', { method: 'POST' }), error => error.status === status && error.retryable === retryable);
    assert.equal(calls, 1);
  }
});
