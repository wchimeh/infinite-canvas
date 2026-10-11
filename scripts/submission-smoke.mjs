import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1500, height: 960 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  await expect(page.locator('.studio-node').first()).toBeVisible();
  await page.locator('.react-flow__controls-fitview').click();
  await page.waitForTimeout(350);
  const point = await page.evaluate(() => {
    const area = document.querySelector('.canvas-area').getBoundingClientRect();
    const cx = (area.left + area.right) / 2, cy = (area.top + area.bottom) / 2;
    return [...document.querySelectorAll('.studio-node header')].map(el => {
      const r = el.getBoundingClientRect();
      return { x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
    }).filter(p => p.x > area.left + 40 && p.x < area.right - 40 && p.y > area.top + 50 && p.y < area.bottom - 30)
      .sort((a, b) => Math.hypot(a.x - cx, a.y - cy) - Math.hypot(b.x - cx, b.y - cy))[0];
  });
  if (!point) throw new Error('No visible node available for submission test');
  await page.mouse.click(point.x, point.y);
  await expect(page.locator('.inspector button.primary')).toBeVisible();
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await page.getByLabel('筛选任务状态').selectOption('failed');
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  let posts = 0;
  await page.route('**/api/v1/runs/estimate', async route => {
    await gate;
    await route.fulfill({ json: { quotes: [], totals: {}, unknownCount: 0, nodeIds: [] } });
  });
  await page.route('**/api/v1/runs', async route => {
    if (route.request().method() !== 'POST') throw new Error('Unexpected run request');
    posts += 1;
    await route.fulfill({ json: { id: 'qa-submitted-run' } });
  });
  await page.route('**/api/v1/runs/qa-submitted-run', route => route.fulfill({ status: 503, json: { message: 'QA read failure' } }));
  const run = page.locator('.header-actions button.primary');
  await run.click();
  await expect(run).toHaveText('检查配置…');
  await expect(run).toBeDisabled();
  await expect(page.getByLabel('当前项目', { exact: true })).toBeDisabled();
  await expect(page.locator('.inspector button.primary')).toBeDisabled();
  await run.evaluate(button => { button.click(); button.click(); });
  release();
  await expect(page.locator('.task-filters')).toBeVisible();
  await expect(page.getByLabel('筛选任务状态')).toHaveValue('all');
  await expect(page.locator('.toast')).toContainText('任务已提交，详情暂未读取');
  await expect(run).toBeEnabled();
  expect(posts).toBe(1);
  await page.unroute('**/api/v1/runs/estimate');
  await page.route('**/api/v1/runs/estimate', route => route.fulfill({ status: 422, json: { message: 'QA 配置检查失败' } }));
  await run.click();
  await expect(page.locator('.toast')).toContainText('QA 配置检查失败');
  await expect(run).toBeEnabled();
  expect(posts).toBe(1);
  expect(errors).toEqual([]);
  console.log('PASS: submission lock, automatic task center, detail failure, preflight failure recovery; no generation requests sent');
} finally { await browser.close(); }
