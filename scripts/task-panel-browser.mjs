import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1050 } });
let showActive = true;
// The backend runs only a local story node; keep its UI active until assertions finish.
await page.route(/\/api\/v1\/(projects\/[^/]+\/tasks|runs\/[^/]+)$/, async route => {
  const response = await route.fetch(); const body = await response.json();
  const tasks = Array.isArray(body) ? body : body.tasks;
  if (showActive && Array.isArray(tasks)) tasks.forEach(task => { task.status = 'queued'; });
  await route.fulfill({ response, json: body });
});
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Task panel QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'story', type: 'studio', position: { x: 100, y: 50 }, data: { kind: 'story.prompt', title: 'Story', config: { prompt: 'local test' } } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  await page.locator('.react-flow__node[data-id="story"] header').click();
  await page.getByRole('button', { name: '收起底部面板', exact: true }).click();
  await page.getByRole('button', { name: '输出故事内容', exact: true }).click();
  const panel = page.locator('#bottom-panel');
  await expect(page.locator('.task-submission-flash')).toHaveCount(1);
  await expect(panel).toHaveClass(/is-collapsed/);
  await expect(page.locator('.tabs button.active')).toContainText('时间线');
  await expect(page.locator('.task-activity-spinner')).toHaveCount(1);
  await expect(page.locator('.task-activity-spinner')).toHaveCSS('animation-name', 'task-processing');
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/task-panel-collapsed.png' });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('.task-activity-spinner')).toHaveCSS('animation-name', 'none');
  await page.reload();
  await expect(panel).toHaveClass(/is-collapsed/);
  showActive = false;
  await expect(page.locator('.task-activity-spinner')).toHaveCount(0, { timeout: 15000 });
  await expect(panel).toHaveClass(/is-collapsed/);
  await page.locator('.tabs button').filter({ hasText: '任务中心' }).click();
  await expect(panel).not.toHaveClass(/is-collapsed/);
  await page.getByLabel('筛选任务状态').selectOption('failed');
  await page.locator('.react-flow__node[data-id="story"] header').click();
  await page.getByRole('button', { name: '输出故事内容', exact: true }).click();
  await expect(page.locator('.task-submission-flash')).toHaveCount(1);
  await expect(page.getByLabel('筛选任务状态')).toHaveValue('failed');
  console.log('PASS: submit/active/completed stay collapsed, manual open, persistence, reduced motion, filters preserved');
} finally { await browser.close(); }
