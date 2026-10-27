import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1050 } });
const edge = id => page.locator(`.react-flow__edge[data-id="${id}"]`);
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Node edge highlight QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [0, 1, 2, 3].map(i => ({ id: `n${i}`, type: 'studio', position: { x: i * 340, y: 100 }, data: { kind: i ? 'text.concat' : 'story.prompt', title: `node${i}`, config: {} } }));
    c.edges = [1, 2, 3].map(i => ({ id: `e${i}`, source: `n${i - 1}`, target: `n${i}`, sourceHandle: 'text', targetHandle: 'text', data: { kind: 'data' } }));
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  });
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await page.locator('.react-flow__node[data-id="n1"] header').click();
  await expect(edge('e1')).toHaveClass(/node-connected-highlight/);
  await expect(edge('e2')).toHaveClass(/node-connected-highlight/);
  await expect(edge('e3')).not.toHaveClass(/node-connected-highlight/);
  await expect(edge('e1').locator('.react-flow__edge-path')).toHaveCSS('stroke', 'rgb(20, 108, 130)');
  await expect(edge('e2').locator('.react-flow__edge-path')).toHaveCSS('stroke-width', '3px');
  await expect(page.locator('.react-flow__edge.selected')).toHaveCount(0);
  await page.keyboard.down('Control'); await page.locator('.react-flow__node[data-id="n3"] header').click(); await page.keyboard.up('Control');
  await expect(page.locator('.node-connected-highlight')).toHaveCount(3);
  const pane = await page.locator('.react-flow__pane').boundingBox();
  await page.mouse.click(pane.x + 25, pane.y + 90);
  await expect(page.locator('.node-connected-highlight')).toHaveCount(0);
  const point = await edge('e2').locator('.react-flow__edge-path').evaluate(path => {
    const p = path.getPointAtLength(path.getTotalLength() / 2);
    const screen = new DOMPoint(p.x, p.y).matrixTransform(path.getScreenCTM());
    return { x: screen.x, y: screen.y };
  });
  await page.mouse.click(point.x, point.y);
  await expect(edge('e2')).toHaveClass(/selected/);
  await expect(page.locator('.node-connected-highlight')).toHaveCount(0);
  await page.locator('.react-flow__node[data-id="n1"] header').click();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    if (c.edges.some(e => e.className?.includes('node-connected-highlight') || e.selected)) throw new Error('Visual highlight leaked into saved selection');
  }, pid);
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/node-edge-highlight.png' });
  console.log('PASS: incoming/outgoing highlight, unrelated edge unchanged, multi-select, deselect, independent edge selection, no persisted highlight');
} finally { await browser.close(); }
