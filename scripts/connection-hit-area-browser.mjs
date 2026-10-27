import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Connection hit area QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = ['asset.image', 'image.character'].map((kind, i) => ({ id: `n${i}`, type: 'studio', position: { x: i * 450 + 20, y: 60 }, data: { kind, title: `node${i}`, config: {} } }));
    c.viewport = { x: 30, y: 30, zoom: 1 };
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  const source = page.locator('.react-flow__node[data-id="n0"] .source');
  const target = page.locator('.react-flow__node[data-id="n1"]');
  await expect(source).toBeVisible();
  for (let i = 0; i < 2; i++) {
    if (i) { await page.locator('.react-flow__controls-zoomout').click(); await page.waitForTimeout(400); }
    const a = await source.boundingBox();
    const b = await target.locator(`.target[data-handleid="${i ? 'image2' : 'image'}"]`).boundingBox();
    const scale = a.width / 14;
    // Start outside the visible dot; release outside the destination hit area.
    await page.mouse.move(a.x + a.width / 2 + 10 * scale, a.y + a.height / 2);
    await page.mouse.down();
    await page.mouse.move(b.x + b.width / 2 - 24 * scale, b.y + b.height / 2, { steps: 20 });
    await page.mouse.up();
    await expect(page.locator('.react-flow__edge')).toHaveCount(i + 1);
    await expect(target.locator('.target')).toHaveCount(i + 3);
  }
  const point = await page.locator('.react-flow__edge-path').first().evaluate(path => {
    const p = path.getPointAtLength(path.getTotalLength() / 2);
    const screen = new DOMPoint(p.x, p.y).matrixTransform(path.getScreenCTM());
    return { x: screen.x, y: screen.y };
  });
  await page.mouse.click(point.x, point.y + 8);
  await expect(page.locator('.react-flow__edge.selected')).toHaveCount(1);
  const selected = page.locator('.react-flow__edge.selected .react-flow__edge-path');
  await expect(selected).toHaveCSS('stroke-width', '3px');
  await expect(selected).toHaveCSS('stroke', 'rgb(20, 108, 130)');
  const handles = await target.locator('.target').evaluateAll(elements => elements.map(el => el.getBoundingClientRect().y));
  expect(handles[2] - handles[1]).toBeGreaterThan(20);
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/connection-hit-area.png' });
  console.log('PASS: off-dot drag, snap outside hit area, dynamic ports at two zooms, wide edge selection');
} finally { await browser.close(); }
