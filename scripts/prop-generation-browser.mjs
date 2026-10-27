import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1100 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/runs', route => route.abort());
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const response = await fetch('/api/v1/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: '道具节点 QA' }) });
    if (!response.ok) throw new Error('project creation failed');
    const project = await response.json();
    localStorage.setItem('canvas-last-project', project.id);
    return project.id;
  });
  await page.reload();
  await page.getByRole('button', { name: '生成道具图', exact: true }).click();
  const target = page.locator('.react-flow__node').filter({ hasText: '生成道具图' });
  await target.locator('header').click();
  await expect(page.getByText('生成一张道具四视图：', { exact: false })).toBeVisible();
  await expect(target.locator('.target[data-handleid="image"]')).toBeVisible();
  await expect(target.locator('.target[data-handleid="image2"]')).toHaveCount(0);
  await page.getByLabel('生成工作流', { exact: true }).selectOption('builtin-image2');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async pid => {
    const canvas = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const target = canvas.nodes.find(node => node.data.kind === 'image.prop');
    if (target.data.config.workflowId !== 'builtin-image2') throw new Error('workflow not saved');
    target.position = { x: 420, y: 0 };
    canvas.nodes.push({ id: 'reference', type: 'studio', position: { x: 0, y: 0 }, data: { kind: 'asset.image', title: '参考图片', config: {} } });
    const response = await fetch(`/api/v1/canvases/${pid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(canvas.version) }, body: JSON.stringify(canvas) });
    if (!response.ok) throw new Error('fixture save failed');
  }, pid);
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click();
  await target.locator('header').click();
  for (let index = 1; index <= 8; index++) {
    await page.locator('.react-flow__controls-fitview').click();
    await page.waitForTimeout(350);
    const port = index === 1 ? 'image' : `image${index}`;
    const start = await page.locator('.react-flow__node[data-id="reference"] .source').boundingBox();
    const end = await target.locator(`.target[data-handleid="${port}"]`).boundingBox();
    await page.mouse.move(start.x + start.width / 2, start.y + start.height / 2);
    await page.mouse.down();
    await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2, { steps: 15 });
    await page.mouse.up();
    await expect(page.locator('.react-flow__edge')).toHaveCount(index);
    if (index < 8) await expect(target.locator(`.target[data-handleid="image${index + 1}"]`)).toBeVisible();
  }
  await expect(target.locator('.target[data-handleid="image9"]')).toHaveCount(0);
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.reload();
  await target.locator('header').click();
  await expect(page.getByLabel('生成工作流', { exact: true })).toHaveValue('builtin-image2');
  await expect(target.locator('.target[data-handleid="image8"]')).toBeVisible();
  await expect(page.locator('.react-flow__edge')).toHaveCount(8);
  expect(errors).toEqual([]);
  console.log('PASS: prop palette, four-view instructions, workflow selection, 8 dynamic image connections and persistence');
} finally {
  await browser.close();
}
