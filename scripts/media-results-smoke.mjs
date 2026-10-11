import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64');
// 浏览器下载不可靠地经过 page.route，使用本地只读代理提供真实 HTTP 文件响应。
const upstream = new URL(url);
const server = createServer(async (req, res) => {
  try {
    if (req.url?.startsWith('/api/v1/assets/qa-image/content')) {
      res.writeHead(200, { 'Content-Type': 'image/png' }); res.end(png); return;
    }
    if (req.method !== 'GET' && req.url !== '/api/v1/session') { res.writeHead(405); res.end(); return; }
    const headers = {};
    for (const key of ['cookie', 'authorization', 'content-type']) if (req.headers[key]) headers[key] = req.headers[key];
    const response = await fetch(new URL(req.url, upstream.origin), { method: req.method, headers });
    const outgoing = {};
    for (const key of ['content-type', 'set-cookie']) if (response.headers.has(key)) outgoing[key] = response.headers.get(key);
    res.writeHead(response.status, outgoing); res.end(Buffer.from(await response.arrayBuffer()));
  } catch { res.writeHead(502); res.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const testUrl = new URL(url); testUrl.hostname = '127.0.0.1'; testUrl.port = String(server.address().port);
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = [], writes = [];
  let imageReady = false, imageReads = 0;
  page.on('pageerror', error => errors.push(error.message));
  const assets = [
    { id: 'qa-image', name: '生成图片.png', mime: 'image/png' },
    { id: 'qa-video', name: '生成视频.mp4', mime: 'video/mp4' },
    { id: 'qa-audio', name: '生成音频.wav', mime: 'audio/wav' },
    { id: 'qa-unknown', name: '未知格式.bin', mime: 'application/octet-stream' },
  ];
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/session')) return route.continue();
    if (route.request().method() !== 'GET') { writes.push(path); return route.fulfill({ json: {} }); }
    if (path.includes('/canvases/')) return route.fulfill({ json: { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 }, version: 1 } });
    if (path.endsWith('/tasks')) return route.fulfill({ json: [{ id: 'qa-media-task', node_id: 'qa-media-node', run_id: 'qa-run', status: 'completed', created_at: 1, updated_at: 1, snapshot: { kind: 'image.generate', config: {} }, output: { assets: [...assets.map(a => a.id), 'qa-missing'] } }] });
    if (/\/projects\/[^/]+\/assets$/.test(path)) return route.fulfill({ json: assets });
    if (path.includes('/assets/qa-image/content')) {
      imageReads++;
      return imageReady ? route.fulfill({ contentType: 'image/png', body: png }) : route.fulfill({ status: 503, body: 'Temporarily unavailable' });
    }
    if (/\/assets\/qa-(video|audio)\/content/.test(path)) return route.fulfill({ status: 404, body: 'Unavailable' });
    return route.continue();
  });
  await page.goto(testUrl.href);
  await page.getByRole('button', { name: /^任务中心/ }).click();
  await page.getByRole('button', { name: '查看结果', exact: true }).click();
  const image = page.getByRole('region', { name: '媒体结果：生成图片.png', exact: true });
  const video = page.getByRole('region', { name: '媒体结果：生成视频.mp4', exact: true });
  const audio = page.getByRole('region', { name: '媒体结果：生成音频.wav', exact: true });
  for (const region of [image, video, audio]) {
    await expect(region.getByRole('alert')).toContainText('预览加载失败');
    await expect(region.getByRole('button', { name: '重新加载' })).toBeVisible();
  }
  imageReady = true;
  await image.getByRole('button', { name: '重新加载' }).click();
  await expect(image.getByRole('img')).toBeVisible();
  await expect(image.getByRole('status')).toHaveCount(0);
  expect(await image.getByRole('img').evaluate(el => el.naturalWidth)).toBe(1);
  expect(imageReads).toBe(2);
  const downloadEvent = page.waitForEvent('download');
  await image.getByRole('link', { name: '下载原文件' }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe('生成图片.png');
  expect(await readFile(await download.path())).toEqual(png);
  await expect(page.getByText('此结果素材已被删除，无法预览。')).toBeVisible();
  await expect(page.getByRole('link', { name: '下载原文件' })).toHaveCount(4);
  await expect(page.getByText('此格式暂不支持预览，可下载原文件查看。')).toBeVisible();
  await page.getByRole('button', { name: '关闭任务结果' }).click();
  await page.getByRole('button', { name: '查看结果', exact: true }).click();
  await expect(image.getByRole('img')).toBeVisible();
  await expect(image.getByRole('alert')).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 960 });
  expect(await page.locator('.task-result-dialog').evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: '.runtime/qa/media-results-mobile.png', fullPage: true });
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
  console.log('PASS: media failure/retry, original download bytes, missing/unknown assets, reopen and mobile; no generation or writes');
} finally { await browser.close(); server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
