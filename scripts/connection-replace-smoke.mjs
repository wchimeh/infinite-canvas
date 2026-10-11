import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const node = (id, kind, x, y) => ({ id, type: 'studio', position: { x, y }, data: { kind, title: id, config: {}, status: 'completed' } });
  const edge = (id, source, target, handle) => ({ id, source, target, sourceHandle: handle, targetHandle: handle, data: { kind: 'data' } });
  let canvas = { nodes: [node('A', 'story.prompt', 0, 0), node('B', 'story.prompt', 0, 320), node('old-image', 'asset.image', 340, 0), node('new-image', 'asset.image', 340, 320), node('target', 'image.generate', 680, 0), node('downstream', 'image.variation', 1020, 0)], edges: [edge('text', 'A', 'target', 'text'), edge('image', 'old-image', 'target', 'image'), edge('downstream-edge', 'target', 'downstream', 'image')], viewport: { x: 20, y: 20, zoom: 0.65 }, version: 1 };
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
  const connect = async (source, output, target, input) => {
    const start = await page.locator(`[data-id="${source}"] .react-flow__handle.source[data-handleid="${output}"]`).boundingBox();
    const end = await page.locator(`[data-id="${target}"] .react-flow__handle.target[data-handleid="${input}"]`).boundingBox();
    await page.mouse.move(start.x + start.width / 2, start.y + start.height / 2);
    await page.mouse.down();
    await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2, { steps: 20 });
    await page.mouse.up();
  };
  const saved = async () => {
    const close = page.getByRole('button', { name: '关闭提示', exact: true });
    if (await close.isVisible()) await close.click();
    await page.getByRole('button', { name: '保存', exact: true }).click();
    await expect(page.locator('.toast')).toContainText('项目已保存');
  };
  const sourceOf = port => canvas.edges.find(e => e.target === 'target' && e.targetHandle === port)?.source;
  await page.goto(url);
  await expect(page.locator('.studio-node')).toHaveCount(6);
  await connect('B', 'text', 'target', 'text');
  await saved();
  expect(canvas.edges.length).toBe(3);
  expect(sourceOf('text')).toBe('B'); expect(sourceOf('image')).toBe('old-image');
  expect(canvas.nodes.find(n => n.id === 'target').data.status).toBe('dirty');
  expect(canvas.nodes.find(n => n.id === 'downstream').data.status).toBe('dirty');
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await saved(); expect(sourceOf('text')).toBe('A');
  expect(canvas.nodes.find(n => n.id === 'target').data.status).toBe('completed');
  await page.getByRole('button', { name: '重做', exact: true }).click();
  await saved(); expect(sourceOf('text')).toBe('B');

  await connect('new-image', 'image', 'target', 'image');
  await saved();
  expect(sourceOf('image')).toBe('new-image'); expect(sourceOf('text')).toBe('B');
  expect(canvas.edges.length).toBe(3);
  const before = JSON.stringify(canvas.edges);
  await connect('new-image', 'image', 'target', 'text');
  await expect(page.locator('.toast')).toContainText('端口类型不匹配');
  await saved(); expect(JSON.stringify(canvas.edges)).toBe(before);
  await connect('downstream', 'image', 'target', 'image');
  await expect(page.locator('.toast')).toContainText('循环依赖');
  await saved(); expect(JSON.stringify(canvas.edges)).toBe(before);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await saved(); expect(sourceOf('image')).toBe('old-image'); expect(sourceOf('text')).toBe('B');
  expect(errors).toEqual([]);
  console.log('PASS: text/image replacement, other input preservation, downstream invalidation, undo/redo and invalid-link atomicity; all writes mocked');
} finally { await browser.close(); }
