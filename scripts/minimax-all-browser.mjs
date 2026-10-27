import { createRequire } from 'node:module';
import { mkdir, readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url, dataDir } = await requireQaSession();
const ffmpeg = path.join(process.env.FFMPEG_DIR, 'ffmpeg.exe');
const files = ['image.png', 'audio.wav', 'video.mp4'].map(name => path.join(dataDir, name));
execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64', '-frames:v', '1', files[0]], { windowsHide: true });
execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '1', files[1]], { windowsHide: true });
execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=24', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '1', '-c:v', 'libx264', '-c:a', 'aac', files[2]], { windowsHide: true });
const media = await Promise.all(files.map(async file => ({ name: path.basename(file), bytes: (await readFile(file)).toString('base64') })));
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1200 } });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/runs', route => route.abort());
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async media => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'MiniMax full reference QA' }))).json();
    const nodes = [], edges = [];
    for (const [i, item] of media.entries()) {
      const port = ['image', 'audio', 'video'][i];
      const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([Uint8Array.from(atob(item.bytes), c => c.charCodeAt(0))]), item.name);
      const asset = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
      nodes.push({ id: port, type: 'studio', position: { x: 0, y: i * 330 }, data: { kind: 'asset.' + port, title: port, config: { assetId: asset.id } } });
      edges.push({ id: port, source: port, target: 'target', sourceHandle: port, targetHandle: port });
      if (port === 'audio') nodes.push({ id: 'other', type: 'studio', position: { x: 800, y: 650 }, data: { kind: 'asset.audio', title: '另一音频', config: { assetId: asset.id } } });
    }
    nodes.push({ id: 'target', type: 'studio', position: { x: 400, y: 100 }, data: { kind: 'video.image_to_video', title: '全能参考', config: { prompt: 'action', seconds: 10 } } });
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    const req = opts('PUT', { ...c, nodes, edges }); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture save failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  }, media);
  await page.reload(); await page.locator('.react-flow__controls-fitview').click();
  const target = page.locator('.react-flow__node[data-id="target"]');
  await target.locator('header').click();
  await expect(page.getByText('MiniMax H3 全能参考（动作迁移）：', { exact: false })).toBeVisible();
  for (const port of ['image', 'audio', 'video']) await expect(target.locator(`.target[data-handleid="${port}2"]`)).toBeVisible();
  await expect(target.locator('.target[data-handleid="videoAudio"]')).toBeVisible();
  await expect(target.locator('.target[data-handleid="videoAudio2"]')).toHaveCount(0);
  async function connect(source, port) {
    await page.waitForTimeout(250);
    const start = await page.locator(`.react-flow__node[data-id="${source}"] .source`).boundingBox();
    const end = await target.locator(`.target[data-handleid="${port}"]`).boundingBox();
    await page.mouse.move(start.x + start.width / 2, start.y + start.height / 2); await page.mouse.down();
    await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2, { steps: 15 }); await page.mouse.up();
  }
  await connect('audio', 'videoAudio');
  await expect(target.locator('.target[data-handleid="videoAudio2"]')).toBeVisible();
  await expect(target.locator('.target[data-handleid="audio3"]')).toHaveCount(0);
  await expect(target.locator('.target[data-handleid="video3"]')).toHaveCount(0);
  await connect('other', 'videoAudio2');
  await expect(target.locator('.target[data-handleid="videoAudio3"]')).toBeVisible();
  await connect('audio', 'videoAudio3');
  await expect(target.locator('.target[data-handleid="videoAudio4"]')).toHaveCount(0);
  await connect('other', 'videoAudio');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const canvas = await page.evaluate(async id => (await fetch(`/api/v1/canvases/${id}`)).json(), pid);
  expect(canvas.edges.filter(e => e.targetHandle === 'videoAudio')).toHaveLength(1);
  expect(canvas.edges.find(e => e.targetHandle === 'videoAudio').source).toBe('other');
  expect(canvas.edges.filter(e => e.targetHandle.startsWith('videoAudio'))).toHaveLength(3);
  await page.reload(); await page.locator('.react-flow__controls-fitview').click(); await target.locator('header').click();
  await expect(target.locator('.target[data-handleid="videoAudio3"]')).toBeVisible();
  await expect(target.getByText('视频音频 3', { exact: true })).toBeVisible();
  await expect(target.getByText('参考音频 1', { exact: true })).toBeVisible();
  await mkdir('.runtime/qa', { recursive: true }); await page.screenshot({ path: '.runtime/qa/minimax-all.png' });
  for (const port of ['videoAudio3', 'videoAudio2']) {
    const edge = canvas.edges.find(e => e.targetHandle === port);
    await page.locator(`.react-flow__edge[data-id="${edge.id}"] .react-flow__edge-interaction`).dispatchEvent('click');
    await page.keyboard.press('Delete');
    await expect(page.locator(`.react-flow__edge[data-id="${edge.id}"]`)).toHaveCount(0);
  }
  await expect(target).toBeVisible();
  await expect(target.locator('.target[data-handleid="videoAudio2"]')).toBeVisible();
  await expect(target.locator('.target[data-handleid="videoAudio3"]')).toHaveCount(0);
  expect(errors).toEqual([]);
  console.log('PASS: distinct audio/video-audio ports, dynamic slots, replacement, deletion and persistence');
} finally { await browser.close(); }
