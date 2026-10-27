import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const request = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', request('POST', { name: 'Recovery QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'story', type: 'studio', position: { x: 100, y: 100 }, data: { kind: 'story.prompt', title: '故事', config: { prompt: 'original' } } }];
    const update = request('PUT', c); update.headers['If-Match'] = String(c.version);
    await fetch(`/api/v1/canvases/${p.id}`, update);
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  });
  await page.reload();
  await page.locator('.react-flow__node[data-id="story"] header').click();
  const input = page.getByLabel('故事内容');
  let writes = 0, failure = 503;
  await page.route(`**/api/v1/canvases/${pid}`, async route => {
    if (route.request().method() !== 'PUT') return route.continue();
    writes++;
    if (failure) return route.fulfill({ status: failure, json: { message: '模拟保存失败' } });
    return route.continue();
  });
  await input.fill('recover without editing again');
  await expect(page.locator('.save-status')).toContainText('保存失败');
  failure = 0;
  await expect(page.locator('.save-status')).toContainText('已保存到本机', { timeout: 10000 });
  expect(writes).toBe(2);
  const saved = await page.evaluate(async id => (await (await fetch(`/api/v1/canvases/${id}`)).json()).nodes[0].data.config.prompt, pid);
  expect(saved).toBe('recover without editing again');

  writes = 0; failure = 409;
  await input.fill('keep this edit on conflict');
  await expect(page.locator('.save-status')).toContainText('保存失败');
  await page.waitForTimeout(3500);
  expect(writes).toBe(1);
  await expect(input).toHaveValue('keep this edit on conflict');
  failure = 0;
  await page.getByRole('button', { name: '重试保存', exact: true }).click();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');

  await page.route(`**/api/v1/projects/${pid}/tasks`, route => route.fulfill({ status: 503, json: { message: '模拟连接中断' } }));
  await expect(page.getByRole('status').filter({ hasText: '连接中断' })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(6000);
  await expect(page.getByRole('status').filter({ hasText: '连接中断' })).toHaveCount(0);
  await page.unroute(`**/api/v1/projects/${pid}/tasks`);
  await expect(page.getByRole('status').filter({ hasText: '连接已恢复' })).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(6000);
  await expect(page.getByRole('status').filter({ hasText: '连接已恢复' })).toHaveCount(0);
  expect(errors).toEqual([]);
  console.log('PASS: automatic save recovery, conflict protection, manual retry, disconnect notification expiry and recovery');
} finally { await browser.close(); }
