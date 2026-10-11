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
  let canvas = { nodes: [{ id: 'existing', type: 'studio', position: { x: -1500, y: -1500 }, data: { kind: 'story.prompt', title: '旧节点', config: {} } }], edges: [], viewport: { x: 140, y: 75, zoom: 0.65 }, version: 1 };
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/session')) return route.continue();
    if (route.request().method() !== 'GET') {
      const body = route.request().postDataJSON() || {};
      if (path.includes('/canvases/')) canvas = { ...body, version: canvas.version + 1 };
      return route.fulfill({ json: path.includes('/canvases/') ? canvas : body });
    }
    if (path.includes('/canvases/')) return route.fulfill({ json: canvas });
    if (path.endsWith('/tasks') || path.endsWith('/assets')) return route.fulfill({ json: [] });
    if (path.endsWith('/people')) return route.fulfill({ json: { characters: [], locations: [], shots: [], version: 1 } });
    return route.continue();
  });
  const add = page.locator('.toolbox-node').filter({ hasText: '故事 / 文本' });
  const coordinates = point => page.locator('.react-flow').evaluate((element, point) => {
    const rect = element.getBoundingClientRect();
    const transform = new DOMMatrix(getComputedStyle(element.querySelector('.react-flow__viewport')).transform);
    return { x: (point.x - rect.x - transform.e) / transform.a, y: (point.y - rect.y - transform.f) / transform.d };
  }, point);
  const savedPosition = async (count, expected) => {
    await page.getByRole('button', { name: '保存', exact: true }).click();
    await expect.poll(() => canvas.nodes.length).toBe(count);
    // Computed CSS matrices round transform decimals; allow less than 0.005 canvas pixels.
    expect(canvas.nodes.at(-1).position.x).toBeCloseTo(expected.x, 2);
    expect(canvas.nodes.at(-1).position.y).toBeCloseTo(expected.y, 2);
    expect(canvas.insertionPosition).toBeUndefined();
  };
  await page.goto(url);
  await expect(add).toBeVisible();
  await expect(page.locator('.react-flow')).toBeVisible();
  const bounds = await page.locator('.react-flow').boundingBox();
  const point = { x: bounds.x + 380, y: bounds.y + 170 };
  const expected = await coordinates(point);
  await page.mouse.click(point.x, point.y);
  await add.click();
  await savedPosition(2, expected);

  // Zoom controls and sidebar clicks must not replace the remembered canvas point.
  await page.getByRole('button', { name: 'Zoom Out', exact: true }).click();
  await expect.poll(() => canvas.viewport.zoom).not.toBe(0.65);
  await add.click();
  await savedPosition(3, expected);

  // A click on a node records its actual canvas coordinates too.
  const header = page.locator(`[data-id="${canvas.nodes.at(-1).id}"] .studio-node header`);
  const headerBounds = await header.boundingBox();
  const nodePoint = { x: Math.floor(headerBounds.x + 35), y: Math.floor(headerBounds.y + 12) };
  const nodeExpected = await coordinates(nodePoint);
  await page.mouse.click(nodePoint.x, nodePoint.y);
  await add.click();
  await savedPosition(4, nodeExpected);

  // Drag/drop has an explicit location and takes priority over the last click.
  const dropPoint = { x: bounds.x + 650, y: bounds.y + 290 };
  const dropExpected = await coordinates(dropPoint);
  const transfer = await page.evaluateHandle(() => { const value = new DataTransfer(); value.setData('application/canvas-kind', 'story.prompt'); return value; });
  await page.locator('.canvas-area').dispatchEvent('drop', { clientX: dropPoint.x, clientY: dropPoint.y, dataTransfer: transfer });
  await savedPosition(5, dropExpected);

  // Reloading a project clears the temporary position, restoring the initial fallback.
  await page.reload();
  await expect(add).toBeVisible();
  await add.click();
  await savedPosition(6, { x: 760, y: 380 });
  expect(errors).toEqual([]);
  console.log('PASS: canvas/node clicks, transformed coordinates, sidebar/zoom isolation, explicit drop placement and reload reset; all writes mocked');
} finally { await browser.close(); }
