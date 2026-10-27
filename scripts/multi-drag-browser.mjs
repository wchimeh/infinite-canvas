import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1050 } });
const node = i => page.locator(`.react-flow__node[data-id="n${i}"]`);
const positions = () => page.locator('.react-flow__node').evaluateAll(nodes => Object.fromEntries(nodes.map(n => [n.dataset.id, n.style.transform])));
async function drag(x, y, dx, dy) {
  await page.mouse.move(x, y); await page.mouse.down();
  await page.mouse.move(x + dx, y + dy, { steps: 15 }); await page.mouse.up();
}
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Multi drag QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [0, 1, 2].map(i => ({ id: `n${i}`, type: 'studio', position: { x: i * 340, y: 100 }, data: { kind: 'story.prompt', title: `node${i}`, config: { prompt: 'local only' } } }));
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  });
  await page.reload(); await expect(node(0)).toBeVisible();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await node(0).locator('header').click();
  await page.keyboard.down('Control'); await node(1).locator('header').click(); await page.keyboard.up('Control');
  await expect(page.locator('.react-flow__node.selected')).toHaveCount(2);
  const before = await positions();
  const box = await node(0).locator('header').boundingBox();
  await drag(box.x + 80, box.y + 15, 55, 70);
  const moved = await positions();
  expect(moved.n0).not.toBe(before.n0); expect(moved.n1).not.toBe(before.n1); expect(moved.n2).toBe(before.n2);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  expect(await positions()).toEqual(before);
  await page.keyboard.down('Shift'); await node(2).locator('header').click(); await page.keyboard.up('Shift');
  await expect(page.locator('.react-flow__node.selected')).toHaveCount(3);
  // Click an unselected node after clearing, then box-select only the first two.
  const pane = await page.locator('.react-flow__pane').boundingBox();
  await page.mouse.click(pane.x + 20, pane.y + 20);
  const a = await node(0).boundingBox(), b = await node(1).boundingBox();
  await drag(a.x - 10, a.y - 12, b.x + b.width - a.x + 20, 60);
  await expect(page.locator('.react-flow__node.selected')).toHaveCount(2);
  const group = await page.locator('.react-flow__nodesselection-rect').boundingBox();
  expect(group).not.toBeNull();
  await drag(group.x + group.width / 2, group.y + 10, 40, 60);
  expect((await positions()).n0).not.toBe(before.n0);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  expect(await positions()).toEqual(before);
  await page.getByRole('button', { name: '重做', exact: true }).click();
  const final = await positions();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const [a, b, untouched] = c.nodes;
    if (Math.abs(b.position.x - a.position.x - 340) > 0.1 || Math.abs(b.position.y - a.position.y) > 0.1) throw new Error('Relative positions changed');
    if (untouched.position.x !== 680 || untouched.position.y !== 100) throw new Error('Unselected node moved');
  }, pid);
  await page.reload(); await expect(node(0)).toBeVisible(); expect(await positions()).toEqual(final);
  console.log('PASS: Ctrl/Shift selection, partial box selection, node/group drag, undo/redo, relative positions, persistence');
} finally { await browser.close(); }
