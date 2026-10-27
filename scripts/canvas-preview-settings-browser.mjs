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
    const settings = await fetch('/api/v1/settings', opts('PUT', { canvasHidePreviews: true, canvasPreviewThreshold: 50 }));
    if (!settings.ok) throw new Error('settings fixture failed');
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Preview threshold QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'story', type: 'studio', position: { x: 200, y: 150 }, data: { kind: 'story.prompt', title: 'Preview QA', config: { prompt: 'Preview content' } } }];
    c.edges = []; c.viewport = { x: 100, y: 100, zoom: 0.4 };
    const request = opts('PUT', c); request.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, request)).ok) throw new Error('canvas fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  const canvas = page.locator('.canvas-area');
  const preview = page.locator('[data-id="story"] .node-body');
  await expect(canvas).toHaveClass(/canvas-overview/);
  await expect(preview).toHaveCSS('visibility', 'hidden');
  const open = async () => { await page.getByLabel('打开工作台设置').click(); await page.getByRole('button', { name: '画布显示', exact: true }).click(); };
  const save = async () => {
    const response = page.waitForResponse(r => r.url().endsWith('/api/v1/settings') && r.request().method() === 'PUT');
    await page.getByRole('button', { name: '保存设置', exact: true }).click();
    expect((await response).ok()).toBe(true);
  };
  const threshold = page.getByLabel('隐藏预览的缩放阈值', { exact: true });
  const toggle = page.getByLabel('缩小时隐藏节点预览', { exact: true });
  await open(); await expect(threshold).toHaveValue('50');
  await threshold.fill('40'); await save();
  await expect(canvas).not.toHaveClass(/canvas-overview/); // Equal to threshold remains visible.
  await expect(preview).toHaveCSS('visibility', 'visible');
  await threshold.fill('80'); await save(); await expect(canvas).toHaveClass(/canvas-overview/);
  await expect(page.locator('.canvas-hint')).toContainText('80%');
  await toggle.uncheck(); await expect(threshold).toBeDisabled(); await save();
  await expect(canvas).not.toHaveClass(/canvas-overview/);
  await page.reload(); await expect(canvas).not.toHaveClass(/canvas-overview/);
  await open(); await expect(toggle).not.toBeChecked(); await expect(threshold).toHaveValue('80');
  await toggle.check(); await save(); await expect(canvas).toHaveClass(/canvas-overview/);
  await threshold.fill('30'); await page.getByLabel('关闭设置').click();
  await expect(canvas).toHaveClass(/canvas-overview/); // Closing does not save drafts.
  await open(); await expect(threshold).toHaveValue('80');
  await threshold.fill('9'); await page.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('10–100');
  await page.getByRole('button', { name: '恢复已保存设置', exact: true }).click();
  await expect(threshold).toHaveValue('80');
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/canvas-preview-settings.png' });
  expect(errors).toEqual([]);
  console.log('PASS: preview threshold boundary, toggle, persistence, unsaved drafts and invalid values');
} finally { await browser.close(); }
