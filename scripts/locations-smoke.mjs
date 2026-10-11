import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = [], generations = [];
  page.on('pageerror', error => errors.push(error.message));
  const locations = [{ name: '旧车站', description: '雨夜车站', layout: '东墙木椅，北面入口', restrictions: '无现代广告' }, { name: '街道', description: '暮色街道', layout: '两侧砖楼，中央石板路', restrictions: '' }];
  let canvas = { nodes: [{ id: 'extract', type: 'studio', selected: true, position: { x: 100, y: 100 }, data: { kind: 'location.extract', title: '提取场景', config: { prompt: '青年从旧车站走向暮色中的街道。' } } }], edges: [], viewport: { x: 0, y: 0, zoom: 1 }, version: 1 };
  let people = { characters: [], locations: [], shots: [], version: 1 };
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname, method = route.request().method();
    if (path.endsWith('/session')) return route.continue();
    if (method !== 'GET') {
      const value = route.request().postDataJSON() || {};
      if (path.endsWith('/runs/estimate')) return route.fulfill({ json: { quotes: [], totals: {}, unknownCount: 0, nodeIds: value.nodeIds } });
      if (path.endsWith('/runs')) { generations.push(value); return route.fulfill({ json: { id: 'qa-batch' } }); }
      if (path.includes('/canvases/')) canvas = { ...value, version: canvas.version + 1 };
      if (path.endsWith('/people')) people = { ...value, version: people.version + 1 };
      return route.fulfill({ json: path.includes('/canvases/') ? canvas : path.endsWith('/people') ? people : value });
    }
    if (path.endsWith('/definitions')) {
      const response = await route.fetch(); const defs = await response.json();
      return route.fulfill({ json: { ...defs, 'location.extract': { displayName: '提取场景', inputs: { text: 'text' }, outputs: { text: 'text' } }, 'image.location': { displayName: '生成场景图', inputs: { text: 'text', image: 'image' }, outputs: { image: 'image' } } } });
    }
    if (path.endsWith('/generation-options')) {
      const response = await route.fetch(); const options = await response.json();
      options.workflows.find(w => w.id === 'builtin-image2').kinds.push('image.location');
      return route.fulfill({ json: options });
    }
    if (path.includes('/canvases/')) return route.fulfill({ json: canvas });
    if (path.endsWith('/runs/qa-batch')) return route.fulfill({ json: { tasks: [] } });
    if (path.endsWith('/people')) return route.fulfill({ json: people });
    const imageNode = canvas.nodes.find(n => n.data.kind === 'image.location');
    const asset = { id: 'qa-role-image', name: '场景图.png', mime: 'image/png', nodeId: imageNode?.id, sha256: '12345678', createdAt: 1 };
    if (path.endsWith('/assets')) return route.fulfill({ json: imageNode ? [asset] : [] });
    if (path.includes('/assets/qa-role-image/')) return route.fulfill({ contentType: 'image/png', body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64') });
    if (path.endsWith('/tasks')) return route.fulfill({ json: [{ id: 'qa-locations', node_id: 'extract', run_id: 'qa', status: 'completed', created_at: 1, snapshot: { kind: 'location.extract', config: canvas.nodes[0].data.config }, output: { text: JSON.stringify(locations), locations } }] });
    return route.continue();
  });
  await page.goto(url);
  await expect(page.getByRole('button', { name: '生成场景图', exact: true })).toBeVisible();
  await expect(page.getByLabel('文本服务商')).toBeVisible();
  await expect(page.getByText('场景草案 · 2 处')).toBeVisible();
  await page.getByRole('button', { name: '确认场景并创建四视图节点' }).click();
  await expect(page.locator('.profile-card')).toHaveCount(2);
  await expect.poll(() => canvas.nodes.filter(n => n.data.kind === 'image.location').length).toBe(2);
  await expect.poll(() => people.locations.length).toBe(2);
  expect(canvas.nodes.find(n => n.data.title === '旧车站 · 场景图').data.config.prompt).toContain('无现代广告');
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await page.getByRole('button', { name: '选择节点', exact: true }).click();
  await page.getByRole('button', { name: '确认场景并创建四视图节点' }).click();
  await expect(page.locator('.toast')).toContainText('这次任务的场景已确认');
  expect(people.locations.length).toBe(2);
  await page.locator('.react-flow__controls-fitview').click();
  const role = page.locator('.studio-node').filter({ hasText: '旧车站 · 场景图' });
  await role.locator('header').click();
  await expect(page.getByLabel('生成工作流')).toBeVisible();
  await page.getByLabel('生成工作流').selectOption('builtin-image2');
  await expect(page.locator('.candidate')).toHaveCount(1);
  await page.locator('.candidate').getByRole('button', { name: '采用', exact: true }).click();
  await expect.poll(() => people.locations.find(c => c.name === '旧车站')?.assetId).toBe('qa-role-image');
  expect(people.locations.find(c => c.name === '街道').assetId).toBeUndefined();
  await page.screenshot({ path: '.runtime/qa/locations-flow.png', fullPage: true });
  expect(generations).toEqual([]);
  const locationIds = canvas.nodes.filter(n => n.data.kind === 'image.location').map(n => n.id).sort();
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await page.getByRole('button', { name: '选择节点', exact: true }).click();
  await page.getByRole('button', { name: /^生成全部场景/ }).click();
  await expect.poll(() => generations.length).toBe(1);
  expect(generations[0].nodeIds.sort()).toEqual(locationIds);
  await expect(page.getByRole('button', { name: /^生成全部场景/ })).toBeEnabled();
  await page.getByRole('button', { name: /^生成全部场景/ }).click();
  await expect.poll(() => generations.length).toBe(2);
  expect(generations[1].nodeIds.sort()).toEqual(locationIds);
  expect(canvas.nodes.filter(n => n.data.kind === 'image.location').length).toBe(2);
  expect(people.locations.length).toBe(2);
  expect(errors).toEqual([]);
  console.log('PASS: location nodes, text provider, review/import, per-location four-view images, duplicate prevention, workflow and adoption; all writes mocked');
} finally { await browser.close(); }
