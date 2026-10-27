import { createRequire } from 'node:module';
import { mkdir, readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url, dataDir } = await requireQaSession();
const videoPath = join(dataDir, 'picker-video.mp4');
execFileSync(process.env.FFMPEG_DIR ? join(process.env.FFMPEG_DIR, process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg') : 'ffmpeg',
  ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=320x180:r=5:d=0.4', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', videoPath], { windowsHide: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1800, height: 1400 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
await page.route('**/api/v1/runs', route => route.abort());
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async videoBytes => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const project = await (await fetch('/api/v1/projects', opts('POST', { name: 'Input picker QA' }))).json();
    const image = document.createElement('canvas'); image.width = 64; image.height = 64;
    const context = image.getContext('2d'); context.fillStyle = '#147d70'; context.fillRect(0, 0, 64, 64);
    const form = new FormData(); form.set('projectId', project.id);
    form.set('file', await new Promise(resolve => image.toBlob(resolve)), '青绿参考.png');
    const upload = await fetch('/api/v1/assets/import', { method: 'POST', body: form });
    if (!upload.ok) throw new Error('fixture image import failed');
    const asset = await upload.json();
    const videoForm = new FormData(); videoForm.set('projectId', project.id);
    videoForm.set('file', new Blob([new Uint8Array(videoBytes)], { type: 'video/mp4' }), '动作视频.mp4');
    const videoUpload = await fetch('/api/v1/assets/import', { method: 'POST', body: videoForm });
    if (!videoUpload.ok) throw new Error('fixture video import failed');
    const videoAsset = await videoUpload.json();
    const canvas = await (await fetch(`/api/v1/canvases/${project.id}`)).json();
    const node = (id, kind, title, x, config = {}) => ({ id, type: 'studio', position: { x, y: 60 }, data: { kind, title, config } });
    canvas.nodes = [node('target', 'video.image_to_video', '目标视频', 470),
      node('image', 'asset.image', '青绿图片', 30, { assetId: asset.id }),
      node('other', 'asset.image', '屏幕外图片', -4000, { assetId: asset.id }),
      node('audio', 'asset.audio', '环境音频', -4000),
      node('video', 'asset.video', '动作视频', -4000, { assetId: videoAsset.id }),
      node('text', 'story.prompt', '剧情文本', -4000, { prompt: '雨后的街道' }),
      node('downstream', 'prompt.video_expand', '不可循环文本', -4000)];
    canvas.edges = [{ id: 'dependency', source: 'target', sourceHandle: 'video', target: 'downstream', targetHandle: 'video', data: { kind: 'data' } }];
    canvas.viewport = { x: 30, y: 30, zoom: 1 };
    const request = opts('PUT', canvas); request.headers['If-Match'] = String(canvas.version);
    if (!(await fetch(`/api/v1/canvases/${project.id}`, request)).ok) throw new Error('fixture canvas failed');
    localStorage.setItem('canvas-last-project', project.id); return project.id;
  }, [...await readFile(videoPath)]);
  await page.reload();
  const target = page.locator('.react-flow__node[data-id="target"]');
  const handle = name => target.locator(`.target[data-handleid="${name}"]`);
  const panel = page.locator('.input-port-picker');
  const open = async name => { await handle(name).hover(); await expect(panel).toBeVisible(); };
  const count = n => expect(page.locator('.canvas-toolbar .muted')).toContainText(`${n} 连线`);
  await open('image');
  await expect(panel.locator('.input-picker-option')).toHaveCount(2);
  await expect(panel.locator('img').first()).toBeVisible();
  await expect.poll(() => panel.locator('img').first().evaluate(img => img.naturalWidth)).toBeGreaterThan(0);
  // Walk from the actual handle to the popup; it must remain open through the gap.
  const box = await panel.boundingBox(); await page.mouse.move(box.x + box.width / 2, box.y + 80, { steps: 12 });
  await page.waitForTimeout(350); await expect(panel).toBeVisible();
  await panel.getByRole('button', { name: '连接：屏幕外图片', exact: true }).click();
  await expect(panel).toHaveCount(0); await count(2);
  await expect(handle('image2')).toBeVisible();
  await open('image'); await expect(panel.getByRole('button', { name: '已连接：屏幕外图片' })).toBeDisabled();
  await panel.getByRole('button', { name: '连接：青绿图片', exact: true }).click(); await count(2);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await open('image'); await expect(panel.getByRole('button', { name: '已连接：屏幕外图片' })).toBeDisabled();
  await panel.getByRole('textbox').fill('不存在'); await expect(panel.getByText('没有匹配的来源，试试其他名称。')).toBeVisible();
  await page.keyboard.press('Escape'); await expect(panel).toHaveCount(0);

  for (const [port, title, total] of [['audio', '环境音频', 3], ['video', '动作视频', 4], ['text', '剧情文本', 5], ['videoAudio', '环境音频', 6]]) {
    await open(port); await expect(panel.locator('.input-picker-option')).toHaveCount(1);
    if (port === 'text') await expect(panel.getByText('雨后的街道')).toBeVisible();
    if (port === 'video') {
      await expect(panel.locator('img')).toHaveCount(1);
      await expect.poll(() => panel.locator('img').evaluate(img => img.naturalWidth)).toBeGreaterThan(0);
      await mkdir('.runtime/qa', { recursive: true });
      await page.screenshot({ path: '.runtime/qa/input-port-picker-video.png' });
    }
    await panel.getByRole('button', { name: `连接：${title}`, exact: true }).click(); await count(total);
  }
  // Keyboard access, search and viewport-bounded popup.
  await handle('image2').focus(); await page.keyboard.press('Enter'); await expect(panel).toBeVisible();
  await expect(panel.getByRole('textbox')).toBeFocused();
  const searchBounds = await panel.locator('.input-picker-search').boundingBox();
  const iconBounds = await panel.locator('.input-picker-search svg').boundingBox();
  const inputBounds = await panel.getByRole('textbox').boundingBox();
  expect(searchBounds.height).toBeLessThan(45);
  expect(Math.abs(iconBounds.y + iconBounds.height / 2 - inputBounds.y - inputBounds.height / 2)).toBeLessThan(3);
  await panel.getByRole('textbox').fill('屏幕外'); await expect(panel.locator('.input-picker-option')).toHaveCount(1);
  const bounds = await panel.boundingBox();
  expect(bounds.x).toBeGreaterThanOrEqual(0); expect(bounds.y + bounds.height).toBeLessThanOrEqual(1400);
  await mkdir('.runtime/qa', { recursive: true }); await page.screenshot({ path: '.runtime/qa/input-port-picker.png' });
  await page.keyboard.press('Escape'); await expect(handle('image2')).toBeFocused();
  await open('image2');
  const pane = await page.locator('.react-flow__pane').boundingBox();
  await page.mouse.move(pane.x + pane.width - 25, pane.y + 40); await page.mouse.wheel(0, -100);
  await expect(panel).toHaveCount(0); await page.waitForTimeout(350);

  // Manual drag still connects and never leaves a picker over the wire.
  const source = page.locator('.react-flow__node[data-id="image"] .source');
  const from = await source.boundingBox(), to = await handle('image2').boundingBox();
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2); await page.mouse.down();
  await page.mouse.move(to.x + to.width / 2, to.y + to.height / 2, { steps: 15 });
  await page.waitForTimeout(350); await expect(panel).toHaveCount(0); await page.mouse.up(); await count(7);
  await open('image3');
  await page.mouse.move(10, 10); await expect(panel).toHaveCount(0);
  await open('image3'); await page.mouse.click(10, 10); await expect(panel).toHaveCount(0);

  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const saved = await page.evaluate(async id => (await fetch(`/api/v1/canvases/${id}`)).json(), pid);
  for (const [port, sourceId] of [['image', 'other'], ['image2', 'image'], ['audio', 'audio'], ['video', 'video'], ['text', 'text'], ['videoAudio', 'audio']]) {
    expect(saved.edges.find(edge => edge.target === 'target' && edge.targetHandle === port)?.source).toBe(sourceId);
  }
  // Delete audio source, verify the true empty state and no stale candidates.
  await page.evaluate(async id => {
    const canvas = await (await fetch(`/api/v1/canvases/${id}`)).json();
    canvas.nodes = canvas.nodes.filter(node => node.id !== 'audio');
    canvas.edges = canvas.edges.filter(edge => edge.source !== 'audio');
    for (let i = 0; i < 25; i++) canvas.nodes.push({ id: `extra${i}`, type: 'studio', position: { x: -4000, y: 100 }, data: { kind: 'asset.image', title: `额外图片 ${i}`, config: {} } });
    const response = await fetch(`/api/v1/canvases/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(canvas.version) }, body: JSON.stringify(canvas) });
    if (!response.ok) throw new Error('empty-state fixture failed');
  }, pid);
  await page.route('**/api/v1/assets/*/thumbnail', route => route.fulfill({ status: 404, body: '' }));
  await page.reload(); await open('audio');
  await expect(panel.getByText('画布上暂无可连接的音频来源。添加对应节点后即可选择。')).toBeVisible();
  await page.keyboard.press('Escape');
  await open('image');
  await expect(panel).toContainText('27 个来源');
  expect(await panel.locator('.input-picker-option').count()).toBeLessThanOrEqual(12);
  await expect(panel.locator('img')).toHaveCount(0);
  const list = panel.locator('.input-picker-list');
  expect(await list.evaluate(el => el.scrollHeight > el.clientHeight)).toBe(true);
  await list.hover(); await page.mouse.wheel(0, 600); await page.waitForTimeout(250);
  await expect(panel).toBeVisible(); expect(await list.evaluate(el => el.scrollTop)).toBeGreaterThan(0);
  await list.evaluate(el => { el.scrollTop = el.scrollHeight; });
  await expect(panel.getByRole('button', { name: '连接：额外图片 24', exact: true })).toBeVisible();
  await panel.getByRole('textbox').fill('额外图片 0');
  await expect(panel.getByRole('button', { name: '连接：额外图片 0', exact: true })).toBeVisible();
  await page.keyboard.press('Escape'); await open('video');
  await expect(panel.locator('img')).toHaveCount(0);
  await expect(panel.locator('.input-picker-preview svg')).toHaveCount(1);
  await expect(panel.getByRole('button', { name: '已连接：动作视频' })).toBeDisabled();
  await page.keyboard.press('Escape');
  const layout = await target.evaluate(node => ({ width: node.offsetWidth, height: node.offsetHeight }));
  for (let i = 0; i < 6; i++) await page.locator('.react-flow__controls-zoomout').click();
  await expect(page.locator('.canvas-overview')).toHaveCount(1);
  await expect(target.locator('.node-body')).toHaveCSS('visibility', 'hidden');
  expect(await target.evaluate(node => ({ width: node.offsetWidth, height: node.offsetHeight }))).toEqual(layout);
  await expect(handle('image')).toBeVisible();
  for (let i = 0; i < 6; i++) await page.locator('.react-flow__controls-zoomin').click();
  await expect(page.locator('.canvas-overview')).toHaveCount(0);
  await expect(target.locator('.node-body')).toHaveCSS('visibility', 'visible');
  expect(errors).toEqual([]);
  console.log('PASS: image/audio/video/text, offscreen sources, previews, cycle filtering, hover bridge, search, replacement, undo, keyboard, manual drag, persistence, empty state');
} finally { await browser.close(); }
