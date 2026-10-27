import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
await page.route('**/api/v1/runs', route => route.abort());
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Checkbox wires QA' }))).json();
    const image = document.createElement('canvas'); image.width = 32; image.height = 32;
    const blob = await new Promise(resolve => image.toBlob(resolve));
    for (let i = 1; i <= 2; i++) {
      const body = new FormData(); body.set('projectId', p.id); body.set('file', blob, `image${i}.png`);
      if (!(await fetch('/api/v1/assets/import', { method: 'POST', body })).ok) throw new Error('import failed');
    }
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'target', type: 'studio', position: { x: 400, y: 100 }, data: { kind: 'image.generate', title: 'Target', config: {} } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    await fetch(`/api/v1/canvases/${p.id}`, req); localStorage.setItem('canvas-last-project', p.id); return p.id;
  });
  await page.reload();
  const target = page.locator('.react-flow__node[data-id="target"]');
  await target.locator('header').click();
  const checkbox = name => page.locator('.reference-list label').filter({ hasText: name }).locator('input');
  await checkbox('image1.png').check();
  await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  await checkbox('image2.png').check();
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);
  await expect(target.locator('.target[data-handleid^="image"]')).toHaveCount(3);
  await checkbox('image1.png').uncheck();
  await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);
  await expect(checkbox('image1.png')).toBeChecked();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  const point = await page.locator('.react-flow__edge-path').first().evaluate(path => {
    const p = path.getPointAtLength(path.getTotalLength() / 2); const screen = new DOMPoint(p.x, p.y).matrixTransform(path.getScreenCTM()); return { x: screen.x, y: screen.y };
  });
  await page.mouse.click(point.x, point.y); await page.keyboard.press('Delete');
  await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  await target.locator('header').click();
  await expect(page.locator('.reference-list input:checked')).toHaveCount(1);
  await checkbox('image1.png').check(); await checkbox('image2.png').check();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    if (c.nodes.length !== 3 || c.edges.length !== 2 || c.nodes.find(n => n.id === 'target').data.config.referenceIds.length) throw new Error('Duplicate nodes or image inputs');
  }, pid);
  await page.reload(); await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await target.locator('header').click();
  await expect(page.locator('.reference-list input:checked')).toHaveCount(2);
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);
  await mkdir('.runtime/qa', { recursive: true }); await page.screenshot({ path: '.runtime/qa/image-reference-selection.png' });
  console.log('PASS: checkbox wires, dynamic image ports, uncheck/delete/undo synchronization, node reuse, persistence, no duplicate input');
} finally { await browser.close(); }
