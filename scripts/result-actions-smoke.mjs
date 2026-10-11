import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const body = '历史任务的完整正文\n第二行：这是本次运行的结果。';
  const node = { id: 'qa-offscreen', type: 'studio', position: { x: 8000, y: 8000 }, data: { kind: 'story.prompt', title: '离屏测试节点', config: {}, status: 'completed' } };
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path.endsWith('/session')) return route.continue();
    if (method !== 'GET') {
      if (path.endsWith('/runs/estimate')) return route.fulfill({ json: { quotes: [], totals: {}, unknownCount: 0, nodeIds: [] } });
      if (path.endsWith('/runs')) return route.fulfill({ json: { id: 'qa-result-run' } });
      const data = route.request().postDataJSON() || {};
      return route.fulfill({ json: { ...data, version: (data.version || 1) + 1 } });
    }
    if (path.includes('/canvases/')) return route.fulfill({ json: { nodes: [node], edges: [], viewport: { x: 0, y: 0, zoom: 1 }, version: 1 } });
    if (path.endsWith('/tasks')) return route.fulfill({ json: [{ id: 'qa-result', run_id: 'qa-run', node_id: node.id, status: 'completed', reused: false, created_at: 1, updated_at: 1, snapshot: { kind: 'story.prompt', config: {} }, output: { text: body } }] });
    if (path.endsWith('/runs/qa-result-run')) return route.fulfill({ status: 503, json: { message: 'QA detail unavailable' } });
    return route.continue();
  });
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await expect(page.locator('.task-row')).toHaveCount(1);
  const search = page.getByRole('searchbox', { name: '搜索当前项目任务' });
  for (const query of ['离屏测试', '  QA-RESULT  ', '已输出故事原文']) {
    await search.fill(query);
    await expect(page.locator('.task-row')).toHaveCount(1);
  }
  await search.fill('不存在的任务');
  await expect(page.locator('.task-row')).toHaveCount(0);
  await page.getByRole('button', { name: '清除筛选' }).click();
  await expect(search).toHaveValue('');
  await expect(page.locator('.task-row')).toHaveCount(1);
  await search.fill('离屏测试');
  await page.getByLabel('筛选任务队列').selectOption('media');
  await expect(page.locator('.task-row')).toHaveCount(0);
  await page.getByRole('button', { name: '清除筛选' }).click();
  await expect(page.getByLabel('筛选任务队列')).toHaveValue('all');
  const before = await page.locator('.canvas-area').evaluate(el => el.clientHeight);
  await page.getByLabel('筛选任务状态').selectOption('completed');
  await page.getByRole('button', { name: '收起底部面板' }).click();
  await expect(page.locator('.task-table')).toBeHidden();
  expect(await page.locator('.canvas-area').evaluate(el => el.clientHeight)).toBeGreaterThan(before + 200);
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await expect(page.getByLabel('筛选任务状态')).toHaveValue('completed');
  for (let i = 0; i < 2; i++) {
    await page.getByRole('button', { name: '选择节点', exact: true }).click();
    await expect(page.locator('.studio-node.selected')).toBeInViewport();
  }
  await page.getByRole('button', { name: '查看结果', exact: true }).click();
  await expect(page.getByLabel('本次任务文本结果')).toHaveText(body);
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.qaCopied = text; } } }));
  await page.getByRole('button', { name: '复制全文' }).click();
  await expect(page.locator('.copy-feedback')).toHaveText('已复制全文');
  expect(await page.evaluate(() => window.qaCopied)).toBe(body);
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw new Error('permission denied'); } } }));
  await page.getByRole('button', { name: '复制全文' }).click();
  await expect(page.locator('.copy-feedback')).toContainText('请选中下方正文手动复制');
  await page.getByRole('button', { name: '关闭任务结果' }).click();
  await page.getByRole('button', { name: '查看结果', exact: true }).click();
  await expect(page.locator('.copy-feedback')).toBeEmpty();
  await page.setViewportSize({ width: 390, height: 960 });
  expect(await page.locator('.task-result-dialog').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.getByRole('button', { name: '关闭任务结果' }).click();
  await page.getByRole('button', { name: '时间线', exact: true }).click();
  await page.getByRole('button', { name: '收起底部面板' }).click();
  await expect(page.locator('.timeline-scroll')).toBeHidden();
  await expect(page.locator('.timeline-meta')).toBeHidden();
  await page.getByRole('button', { name: '展开底部面板' }).click();
  await expect(page.locator('.timeline-scroll')).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.getByRole('button', { name: '收起底部面板' }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: '展开底部面板' })).toHaveAttribute('aria-expanded', 'false');
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await page.getByRole('button', { name: '选择节点', exact: true }).click();
  await page.getByRole('button', { name: '收起底部面板' }).click();
  await page.locator('.header-actions button.primary').click();
  await expect(page.locator('.task-table')).toBeVisible();
  await expect(page.getByRole('button', { name: '收起底部面板' })).toHaveAttribute('aria-expanded', 'true');
  await page.addInitScript(() => {
    const get = Storage.prototype.getItem, set = Storage.prototype.setItem;
    Storage.prototype.getItem = function(key) { if (key === 'canvas-bottom-collapsed') throw new Error('Storage blocked'); return get.call(this, key); };
    Storage.prototype.setItem = function(key, value) { if (key === 'canvas-bottom-collapsed') throw new Error('Storage blocked'); return set.call(this, key, value); };
  });
  await page.reload();
  await page.getByRole('button', { name: '收起底部面板' }).click();
  await expect(page.getByRole('button', { name: '展开底部面板' })).toBeVisible();
  await page.getByRole('button', { name: '展开底部面板' }).click();
  expect(errors).toEqual([]);
  console.log('PASS: task search/reset, persisted collapse and storage failure, focus, copy, submission expands; all writes mocked');
} finally { await browser.close(); }
