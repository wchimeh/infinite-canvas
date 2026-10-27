import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
let confirms = 0, submissions = 0, estimates = 0, estimateFails = false;
const errors = []; page.on('pageerror', e => errors.push(e.message));
page.on('dialog', async dialog => { confirms++; await dialog.dismiss(); });
// Never send real generation requests during this test.
await page.route('**/api/v1/runs/estimate', route => {
  estimates++;
  return route.fulfill(estimateFails ? { status: 400, json: { message: '预算检查未通过' } } : { json: { nodeIds: ['script'], totals: {}, unknownCount: 1, quotes: [{ provider: 'text', basis: 'unknown' }] } });
});
await page.route('**/api/v1/runs', route => { submissions++; return route.fulfill({ json: { id: 'qa-cost-run' } }); });
await page.route('**/api/v1/runs/qa-cost-run', route => route.fulfill({ json: { tasks: [] } }));
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    await fetch('/api/v1/settings', opts('PUT', { confirmGenerationCost: true }));
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '费用提示验收' }))).json();
    await fetch(`/api/v1/projects/${p.id}/settings`, opts('PUT', { cloudEnabled: true }));
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'script', type: 'studio', position: { x: 80, y: 50 }, selected: true, data: { kind: 'script.expand', title: '剧本', config: { prompt: 'test' } } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  const run = page.getByRole('button', { name: '运行节点', exact: true });
  await run.click(); await expect.poll(() => confirms).toBe(1); expect(submissions).toBe(0);
  const open = async () => { await page.getByLabel('打开工作台设置').click(); await page.getByRole('button', { name: '费用与并发', exact: true }).click(); };
  const toggle = page.getByLabel('生成前显示费用提示');
  const save = async () => { await page.getByRole('button', { name: '保存设置', exact: true }).click(); await expect(page.getByText('设置已保存', { exact: true })).toBeVisible(); };
  await open(); await expect(toggle).toBeChecked(); await toggle.uncheck(); await save();
  await page.getByLabel('关闭设置').click();
  await run.click(); await expect.poll(() => submissions).toBe(1); expect(confirms).toBe(1);
  await page.reload();
  await page.locator('.react-flow__node header').click({ position: { x: 20, y: 12 } });
  await open(); await expect(toggle).not.toBeChecked(); await page.getByLabel('关闭设置').click();
  estimateFails = true;
  await run.click(); await expect(page.getByText('预算检查未通过', { exact: true })).toBeVisible(); expect(submissions).toBe(1);
  estimateFails = false;
  await open(); await toggle.check(); await save(); await page.getByLabel('关闭设置').click();
  await run.click(); await expect.poll(() => confirms).toBe(2); expect(submissions).toBe(1);
  expect(estimates).toBe(4); expect(errors).toEqual([]);
  console.log('PASS: 默认提示、设置关闭立即生效、刷新保留、再次开启提示、估算失败仍阻止提交；所有提交均被模拟。');
} finally { await browser.close(); }
