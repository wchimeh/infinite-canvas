import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  let canvas = { nodes: [{ id: 'video', type: 'studio', selected: true, position: { x: 100, y: 100 }, data: { kind: 'video.image_to_video', title: '生成视频', config: { workflowId: 'omni', prompt: '测试全能参考' } } }], edges: [], viewport: { x: 0, y: 0, zoom: 1 }, version: 1 };
  const assets = ['image', 'video', 'audio'].map(type => ({ id: type, name: `${type}-reference`, mime: `${type}/fixture`, sha256: '12345678', createdAt: 1 }));
  assets.splice(1, 0, { ...assets[0], id: 'second-image', name: 'second-image-reference' });
  canvas.nodes.push(...['first', 'second', 'replacement'].map((id, index) => ({ id, type: 'studio', selected: false, position: { x: index === 1 ? -260 : -600, y: index === 2 ? 360 : 0 }, data: { kind: 'asset.image', title: id, config: { assetId: index === 1 ? 'second-image' : 'image' } } })));
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/session')) return route.continue();
    if (route.request().method() !== 'GET') {
      const body = route.request().postDataJSON() || {};
      if (path.includes('/canvases/')) canvas = { ...body, version: canvas.version + 1 };
      return route.fulfill({ json: path.includes('/canvases/') ? canvas : body });
    }
    if (path.includes('/canvases/')) return route.fulfill({ json: canvas });
    if (path.endsWith('/definitions')) {
      const response = await route.fetch(); const definitions = await response.json();
      definitions['video.image_to_video'] = { ...definitions['video.image_to_video'], displayName: '生成视频', inputs: { text: 'text', ...Object.fromEntries([['image', 9], ['audio', 3], ['video', 3]].flatMap(([port, count]) => Array.from({ length: count }, (_, i) => [port + (i ? i + 1 : ''), port]))) } };
      return route.fulfill({ json: definitions });
    }
    if (path.endsWith('/generation-options')) return route.fulfill({ json: { textServices: [], workflows: [{ id: 'builtin-minimax-h3', name: 'MiniMax H3 · 自动匹配参考数量', builtin: 'minimax_h3', enabled: true, kinds: ['video.image_to_video'], version: 1 }, { id: 'omni', name: '全能参考', enabled: true, kinds: ['video.image_to_video'], version: 1 }] } });
    if (path.endsWith('/tasks')) return route.fulfill({ json: [] });
    if (path.endsWith('/assets')) return route.fulfill({ json: assets });
    if (path.includes('/assets/')) return route.fulfill({ contentType: 'image/png', body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64') });
    return route.continue();
  });
  await page.goto(url);
  await expect(page.getByRole('button', { name: '生成视频', exact: true })).toHaveCount(1);
  await expect(page.getByRole('button', { name: '视频音效', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: '对白 / 配音', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: '音频素材', exact: true })).toBeVisible();
  await expect(page.getByLabel('生成工作流')).toHaveValue('omni');
  await expect(page.getByLabel('视频模型', { exact: true })).toHaveCount(0);
  const cardDuration = page.locator('[data-id="video"]').getByLabel('生成时长（秒）');
  const inspectorDuration = page.locator('.inspector').getByLabel('生成时长（秒）');
  await expect(cardDuration).toHaveValue('5');
  await cardDuration.fill('8');
  await cardDuration.press('Enter');
  await expect(inspectorDuration).toHaveValue('8');
  await inspectorDuration.fill('');
  await inspectorDuration.press('Tab');
  await expect(inspectorDuration).toHaveValue('8');
  await inspectorDuration.fill('12');
  await inspectorDuration.press('Tab');
  await expect(cardDuration).toHaveValue('12');
  await cardDuration.fill('40');
  await cardDuration.press('Enter');
  await expect(inspectorDuration).toHaveValue('30');
  await cardDuration.fill('0');
  await cardDuration.press('Enter');
  await expect(inspectorDuration).toHaveValue('1');
  await cardDuration.fill('8');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.nodes[0].data.config.seconds).toBe(8);
  await page.reload();
  await expect(cardDuration).toHaveValue('8');
  await page.locator('[data-id="video"] header').click();
  await expect(inspectorDuration).toHaveValue('8');
  await page.getByLabel('生成工作流').selectOption('');
  await expect(page.getByLabel('生成工作流')).toHaveValue('builtin-minimax-h3');
  await expect(page.getByText(/默认按素材数量匹配 workflow_json_new.py/)).toBeVisible();
  await expect(page.getByRole('button', { name: '运行节点', exact: true })).toBeEnabled();
  await page.getByLabel('生成工作流').selectOption('omni');
  await expect(page.getByRole('button', { name: '运行节点', exact: true })).toBeEnabled();
  await expect(page.locator('[data-id="video"] .react-flow__handle.target')).toHaveCount(4);
  await expect(page.getByRole('button', { name: '添加图片输入', exact: true })).toHaveCount(0);
  for (const asset of assets) await page.getByRole('checkbox', { name: `${asset.name} ${asset.sha256}`, exact: true }).check();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.nodes[0].data.config.referenceIds).toEqual(['image', 'second-image', 'video', 'audio']);
  await page.locator('.react-flow__controls-fitview').click();
  await page.waitForTimeout(350);
  const connect = async (source, port) => {
    const start = await page.locator(`[data-id="${source}"] .react-flow__handle.source`).boundingBox();
    const end = await page.locator(`[data-id="video"] .react-flow__handle.target[data-handleid="${port}"]`).boundingBox();
    await page.mouse.move(start.x + start.width / 2, start.y + start.height / 2);
    await page.mouse.down(); await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2, { steps: 20 }); await page.mouse.up();
  };
  await connect('first', 'image');
  await expect(page.locator('[data-id="video"] .react-flow__handle.target[data-handleid="image2"]')).toBeVisible();
  await connect('second', 'image2');
  await expect(page.locator('[data-id="video"] .react-flow__handle.target[data-handleid="image3"]')).toBeVisible();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.edges.length).toBe(2);
  expect(canvas.edges.find(edge => edge.targetHandle === 'image')?.source).toBe('first');
  expect(canvas.edges.find(edge => edge.targetHandle === 'image2')?.source).toBe('second');
  // The previously offscreen reference now has measured media dimensions.
  await page.locator('.react-flow__controls-fitview').click();
  await page.waitForTimeout(350);
  await connect('replacement', 'image2');
  await page.screenshot({ path: '.runtime/qa/video-multiple-images.png', fullPage: true });
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.edges.find(edge => edge.targetHandle === 'image2')?.source).toBe('replacement');
  expect(canvas.edges.find(edge => edge.targetHandle === 'image')?.source).toBe('first');
  expect(canvas.edges.length).toBe(2);
  await page.screenshot({ path: '.runtime/qa/video-multiple-images.png', fullPage: true });
  await page.getByRole('button', { name: '音频素材', exact: true }).click();
  await expect(page.getByLabel('锁定素材版本')).toBeVisible();
  await page.getByLabel('锁定素材版本').selectOption('audio');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.nodes.find(node => node.data.kind === 'asset.audio')?.data.config.assetId).toBe('audio');
  const audioId = canvas.nodes.find(node => node.data.kind === 'asset.audio').id;
  canvas.nodes.push({ id: 'video-source', type: 'studio', position: { x: -900, y: 0 }, data: { kind: 'asset.video', title: 'Video reference', config: { assetId: 'video' } } });
  for (const level of [1, 2, 9]) {
    canvas.nodes.forEach(node => { node.selected = node.id === 'video'; });
    canvas.edges = [['image', 9, 'first'], ['audio', 3, audioId], ['video', 3, 'video-source']].flatMap(([port, limit, source]) => Array.from({ length: Math.min(level, limit) }, (_, index) => ({ id: `${port}-${index}`, source, target: 'video', sourceHandle: port, targetHandle: port + (index ? index + 1 : ''), data: { kind: 'data' } })));
    await page.reload();
    for (const [port, limit] of [['image', 9], ['audio', 3], ['video', 3]]) await expect(page.locator(`[data-id="video"] .port.${port} .react-flow__handle.target`)).toHaveCount(Math.min(level + 1, limit));
    await expect(page.getByRole('button', { name: '添加图片输入', exact: true })).toHaveCount(0);
  }
  // Removing an earlier connection must not hide a connected high-numbered input.
  canvas.edges = canvas.edges.filter(edge => !['image', 'audio', 'video'].includes(edge.targetHandle));
  await page.reload();
  await expect(page.locator('[data-id="video"] .react-flow__handle.target[data-handleid="image9"]')).toHaveCount(1);
  await expect(page.locator('[data-id="video"] .react-flow__handle.target[data-handleid="audio3"]')).toHaveCount(1);
  await expect(page.locator('[data-id="video"] .react-flow__handle.target[data-handleid="video3"]')).toHaveCount(1);
  expect(errors).toEqual([]);
  console.log('PASS: single video generation entry, audio asset only, multimedia ports/reference selection and audio binding; all writes mocked');
} finally { await browser.close(); }
