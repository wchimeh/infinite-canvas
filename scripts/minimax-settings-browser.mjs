import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.route('**/api/v1/runs', route => route.abort());
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'MiniMax settings QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'video', type: 'studio', position: { x: 250, y: 100 }, data: { kind: 'video.image_to_video', title: 'Video QA', config: {} } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('save fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  await page.locator('[data-id="video"] header').click();
  const field = name => page.locator('.inspector').getByLabel(name, { exact: true });
  await expect(field('画面比例')).toHaveValue('16:9 (Widescreen)');
  await expect(field('画面比例').locator('option')).toHaveCount(8);
  await expect(field('百万像素（MP）')).toHaveValue('0.4');
  await expect(field('尺寸倍数')).toHaveValue('32');
  await expect(field('采样步数')).toHaveValue('8');
  await expect(field('种子模式')).toHaveValue('random');
  await expect(field('固定种子')).toHaveCount(0);
  await field('画面比例').selectOption('9:16 (Portrait Widescreen)');
  for (const [name, value] of [['百万像素（MP）', '0.8'], ['尺寸倍数', '64'], ['采样步数', '12']]) {
    await field(name).fill(value); await field(name).press('Tab');
  }
  await field('采样步数').fill(''); await field('采样步数').press('Tab');
  await expect(field('采样步数')).toHaveValue('12');
  await field('种子模式').selectOption('fixed');
  await field('固定种子').fill('123456'); await field('固定种子').press('Tab');
  await field('种子模式').selectOption('random'); await expect(field('固定种子')).toHaveCount(0);
  await field('种子模式').selectOption('fixed'); await expect(field('固定种子')).toHaveValue('123456');
  await field('生成服务').selectOption('comfyui'); await expect(field('画面比例')).toHaveCount(0);
  await field('生成服务').selectOption('runninghub'); await expect(field('尺寸倍数')).toHaveValue('64');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.reload(); await page.locator('[data-id="video"] header').click();
  for (const [name, value] of [['画面比例', '9:16 (Portrait Widescreen)'], ['百万像素（MP）', '0.8'], ['尺寸倍数', '64'], ['采样步数', '12'], ['种子模式', 'fixed'], ['固定种子', '123456']]) await expect(field(name)).toHaveValue(value);
  await field('固定种子').scrollIntoViewIfNeeded();
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/minimax-settings.png' });
  expect(errors).toEqual([]);
  console.log('PASS: MiniMax defaults, eight ratios, parameter edits, invalid draft recovery, seed modes, provider visibility, persistence');
} finally { await browser.close(); }
