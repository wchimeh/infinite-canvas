import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1680, height: 1050 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
async function connect(source, target, output, input) {
  const from = page.locator(`.react-flow__node[data-id="${source}"] .react-flow__handle.source[data-handleid="${output}"]`);
  const to = page.locator(`.react-flow__node[data-id="${target}"] .react-flow__handle.target[data-handleid="${input}"]`);
  const a = await from.boundingBox(), b = await to.boundingBox();
  if (!a || !b) throw new Error('Missing connection handle');
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 20 });
  await page.mouse.up();
}
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const p = await (await fetch('/api/v1/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: '拼接与角色连接点验收' }) })).json();
    localStorage.setItem('canvas-last-project', p.id);
    return p.id;
  });
  await page.reload();
  await page.locator('.toolbox-node').filter({ hasText: '文本拼接' }).click();
  await expect(page.getByLabel('文本分隔方式')).toHaveValue('newline');
  await expect(page.getByLabel('生成服务', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const joinId = await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const join = c.nodes[0]; join.position = { x: 380, y: 20 };
    const node = (id, kind, x, y, config = {}) => ({ id, type: 'studio', position: { x, y }, data: { kind, title: id, config } });
    c.nodes = [node('a', 'story.prompt', 0, 0, { prompt: '甲' }), node('b', 'story.prompt', 0, 320, { prompt: '乙' }), join,
      node('role', 'image.character', 760, 320), node('img', 'asset.image', 380, 650)];
    await fetch(`/api/v1/canvases/${pid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(c.version) }, body: JSON.stringify(c) });
    return join.id;
  }, pid);
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(350);
  const join = page.locator(`.react-flow__node[data-id="${joinId}"]`);
  await expect(join.locator('.target')).toHaveCount(1);
  await connect('a', joinId, 'text', 'text');
  await expect(join.locator('.target')).toHaveCount(2);
  await connect('b', joinId, 'text', 'text2');
  await expect(join.locator('.target')).toHaveCount(3);
  await join.locator('header').click();
  await page.getByLabel('文本分隔方式').selectOption('custom');
  await page.getByLabel('自定义分隔符').fill(' + ');
  await page.getByRole('button', { name: '拼接文本', exact: true }).click();
  await expect(join.locator('.node-result-text')).toContainText('甲 + 乙', { timeout: 15000 });
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await page.reload();
  await expect(join.locator('.target')).toHaveCount(3);
  await join.locator('header').click();
  await expect(page.getByLabel('自定义分隔符')).toHaveValue(' + ');
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(350);
  const role = page.locator('.react-flow__node[data-id="role"]');
  await expect(role.locator('.target')).toHaveCount(2);
  await connect('img', 'role', 'image', 'image');
  await expect(role.locator('.target')).toHaveCount(3);
  await connect('img', 'role', 'image', 'image2');
  await expect(role.locator('.target')).toHaveCount(4);
  await connect('b', joinId, 'text', 'text');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async ({ pid, joinId }) => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const connected = c.edges.filter(e => e.target === joinId && e.targetHandle === 'text');
    if (connected.length !== 1 || connected[0].source !== 'b') throw new Error('Reconnect must replace previous input');
    c.edges = [
      ...Array.from({ length: 10 }, (_, i) => ({ id: `t${i}`, source: 'a', target: joinId, sourceHandle: 'text', targetHandle: 'text' + (i ? i + 1 : ''), data: { kind: 'data' } })),
      ...Array.from({ length: 8 }, (_, i) => ({ id: `i${i}`, source: 'img', target: 'role', sourceHandle: 'image', targetHandle: 'image' + (i ? i + 1 : ''), data: { kind: 'data' } })),
    ];
    const saved = await fetch(`/api/v1/canvases/${pid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(c.version) }, body: JSON.stringify(c) });
    if (!saved.ok) throw new Error('Cannot persist full input fixture');
  }, { pid, joinId });
  await page.reload();
  await expect(join.locator('.target')).toHaveCount(10);
  await expect(role.locator('.target')).toHaveCount(9); // text + eight images
  await expect(join.locator('[data-handleid="text11"]')).toHaveCount(0);
  await expect(role.locator('[data-handleid="image9"]')).toHaveCount(0);
  expect(errors).toEqual([]);
  console.log('PASS: 本地文本拼接、自定义分隔符保存重开、动态文本口、角色多参考图自动扩展；未调用云端。');
} finally { await browser.close(); }
