import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { requireQaSession } from './qa-session.mjs';

test('写入验收拒绝缺省、日常目录和非本机服务，仅接受独立 QA 清单', async () => {
  await assert.rejects(requireQaSession({}), /隔离/);
  const root = await mkdtemp(path.resolve('.runtime/qa-guard-'));
  const dataDir = path.join(root, 'data'), configDir = path.join(root, 'config');
  await mkdir(dataDir); await mkdir(configDir);
  const file = path.join(root, 'session.json');
  const env = { CANVAS_QA: '1', CANVAS_SESSION_FILE: file };
  const valid = { qa: true, dataDir, configDir, url: 'http://127.0.0.1:54321/#token=test-only' };
  try {
    await writeFile(file, JSON.stringify(valid));
    assert.equal((await requireQaSession(env)).url, valid.url);
    for (const patch of [{ qa: false }, { dataDir: path.resolve('data') }, { url: 'http://127.0.0.1:5173/' }, { url: 'https://example.com/' }]) {
      await writeFile(file, JSON.stringify({ ...valid, ...patch }));
      await assert.rejects(requireQaSession(env), /隔离/);
    }
  } finally { await rm(root, { recursive: true, force: true }); }
});
