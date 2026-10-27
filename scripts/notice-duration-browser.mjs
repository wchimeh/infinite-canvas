import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const post = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', post('POST', { name: '提示与时长验收' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [
      { id: 'expand', type: 'studio', position: { x: 0, y: 0 }, data: { kind: 'prompt.video_expand', title: '扩写', config: { prompt: 'scene', seconds: 5 } } },
      { id: 'video', type: 'studio', position: { x: 380, y: 0 }, data: { kind: 'video.image_to_video', title: '视频', config: { seconds: 5, durationSource: 'upstream' } } },
    ];
    c.edges = [{ id: 'text', source: 'expand', target: 'video', sourceHandle: 'text', targetHandle: 'text', data: { kind: 'data' } }];
    const request = post('PUT', c); request.headers['If-Match'] = String(c.version);
    await fetch(`/api/v1/canvases/${p.id}`, request);
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  const video = page.locator('.react-flow__node[data-id="video"]');
  await expect(video).toBeVisible();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(350);
  await video.locator('header').click();
  await video.getByLabel('生成时长（秒）').fill('10');
  await video.getByLabel('生成时长（秒）').press('Tab');
  await expect(video.getByLabel('生成时长（秒）')).toHaveValue('10');
  await expect(page.getByLabel('跟随上游时长')).not.toBeChecked();
  await page.locator('.react-flow__node[data-id="expand"] header').click({ position: { x: 25, y: 15 } });
  await page.locator('.inspector textarea').fill('updated scene');
  await expect(video.getByLabel('生成时长（秒）')).toHaveValue('10');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('项目已保存');
  await page.reload();
  await video.locator('header').click();
  await expect(page.locator('.inspector').getByLabel('生成时长（秒）')).toHaveValue('10');
  await page.getByLabel('跟随上游时长').check();
  await expect(video.getByLabel('生成时长（秒）')).toHaveValue('5');
  await page.locator('.inspector').getByLabel('生成时长（秒）').fill('10');
  await page.locator('.inspector').getByLabel('生成时长（秒）').press('Tab');
  await expect(video.getByLabel('生成时长（秒）')).toHaveValue('10');
  await expect(page.getByLabel('跟随上游时长')).not.toBeChecked();

  const save = page.getByRole('button', { name: '保存', exact: true });
  await save.click(); await expect(page.getByRole('status')).toBeVisible();
  await page.waitForTimeout(5300);
  await expect(page.getByRole('status')).toHaveCount(0);
  await save.click(); await expect(page.getByRole('status')).toBeVisible();
  await page.waitForTimeout(3000);
  await save.click();
  await page.waitForTimeout(2500);
  await expect(page.getByRole('status')).toBeVisible();
  await page.waitForTimeout(2800);
  await expect(page.getByRole('status')).toHaveCount(0);
  await save.click(); await page.getByRole('button', { name: '关闭提示', exact: true }).click();
  await expect(page.getByRole('status')).toHaveCount(0);
  expect(errors).toEqual([]);
  console.log('PASS: 视频10秒手动优先、上下游编辑及重开保持、恢复跟随5秒；提示5秒关闭、重复重计时、手动关闭。');
} finally { await browser.close(); }
