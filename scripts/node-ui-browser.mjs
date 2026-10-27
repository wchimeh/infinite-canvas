import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const sample = '.runtime/node-ui-sample.mp4';
const ffmpeg = process.env.FFMPEG_DIR ? join(process.env.FFMPEG_DIR, 'ffmpeg.exe') : 'ffmpeg';
const encoded = spawnSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=white:s=160x120:r=25', '-t', '3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', sample]);
if (encoded.status !== 0) throw new Error(`FFmpeg fixture failed: ${encoded.stderr}`);
const videoBytes = [...await readFile(sample)];
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const { pid, assetId } = await page.evaluate(async bytes => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '全部节点界面验收' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([new Uint8Array(bytes)], { type: 'video/mp4' }), 'three-seconds.mp4');
    const asset = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
    if (!asset.id) throw new Error('video import failed');
    const defs = [['select', 'shots.select'], ['expand', 'prompt.video_expand'], ['audio', 'asset.audio'], ['tts', 'audio.tts'], ['concat', 'text.concat'], ['script', 'script.expand']];
    c.nodes = defs.map(([id, kind], index) => ({ id, type: 'studio', position: { x: index % 3 * 380, y: Math.floor(index / 3) * 420 }, data: { kind, title: id, config: id === 'select' ? { selectedShot: { durationMs: 10000 }, shotIndex: 0 } : { prompt: 'Scene', seconds: 5 } } }));
    c.nodes.push(...['asset.video', 'video.image_to_video'].map((kind, i) => ({ id: `film${i}`, type: 'studio', position: { x: 1140, y: i * 420 }, data: { kind, title: `film${i}`, config: { assetId: asset.id, seconds: 20 } } })));
    c.edges = [{ id: 'duration', source: 'select', target: 'expand', sourceHandle: 'text', targetHandle: 'text' }, { id: 'voice', source: 'audio', target: 'tts', sourceHandle: 'audio', targetHandle: 'audio' }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    const result = await fetch(`/api/v1/canvases/${p.id}`, req);
    if (!result.ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
    return { pid: p.id, assetId: asset.id };
  }, videoBytes);
  // Only mock the task listing: no provider, generation, or submit request is made.
  await page.route(`**/api/v1/projects/${pid}/tasks`, route => route.fulfill({ json: [
    ['concat', 'text.concat'], ['select', 'shots.select'], ['script', 'script.expand'],
  ].map(([id, kind]) => ({ id: `qa-${id}`, node_id: id, created_at: 1, updated_at: 1, status: 'completed', snapshot: { kind }, output: { text: 'QA result' }, deps: [] })) }));
  await page.reload();
  await expect(page.locator('.react-flow__node[data-id="expand"]')).toBeVisible();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  const selectNode = async id => { await page.locator(`.react-flow__node[data-id="${id}"] header`).click({ position: { x: 20, y: 12 } }); };
  await selectNode('expand');
  await expect(page.getByLabel('扩写目标时长（秒）')).toBeDisabled();
  await expect(page.getByLabel('扩写目标时长（秒）')).toHaveValue('10');
  await expect(page.locator('.duration-source')).toContainText('select');
  await selectNode('tts');
  const consent = page.getByRole('checkbox', { name: '我已获得参考声音的使用授权' });
  await expect(consent).toBeVisible(); await consent.check(); await expect(consent).toBeChecked();
  for (const id of ['film0', 'film1']) {
    await selectNode(id);
    const approve = page.getByRole('button', { name: '批准并加入时间线', exact: true });
    await expect(approve).toBeEnabled();
    await expect(page.locator('.inspector')).toContainText('素材实际时长 3 秒');
    if (id === 'film1') {
      await page.locator('.inspector').getByLabel('生成时长（秒）').fill('30');
      await page.locator('.inspector').getByLabel('生成时长（秒）').press('Tab');
    }
    await approve.click();
  }
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => page.evaluate(async pid => (await (await fetch(`/api/v1/projects/${pid}/timeline`)).json()).clips.map(c => c.durationMs), pid)).toEqual([3000, 3000]);
  await page.getByRole('button', { name: '任务中心', exact: true }).click();
  await page.getByLabel('筛选任务队列').selectOption('local');
  await expect(page.locator('.task-row')).toHaveCount(2);
  await page.getByLabel('筛选任务队列').selectOption('text');
  await expect(page.locator('.task-row')).toHaveCount(1);
  await expect(page.locator('.task-row')).toContainText('script');
  await page.getByRole('button', { name: '时间线', exact: true }).click();
  for (const width of [1440, 900, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    const box = await page.locator('.bottom-heading').boundingBox();
    const buttons = await page.locator('.timeline-meta > *').all();
    for (const button of buttons) {
      if (!await button.isVisible()) continue;
      const b = await button.boundingBox();
      expect(b.y + b.height).toBeLessThanOrEqual(box.y + box.height + 1);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `.runtime/node-ui-${width}.png`, fullPage: true });
  }
  expect(errors).toEqual([]);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route(`**/api/v1/assets/${assetId}/content`, route => route.abort());
  await page.reload();
  await page.locator('.react-flow__node[data-id="film0"]').waitFor();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await selectNode('film0');
  await expect(page.getByRole('button', { name: '批准并加入时间线', exact: true })).toBeDisabled();
  console.log('PASS: 本地任务分类、连线音频授权、扩写继承来源、三种视口工具栏；3秒视频导入/已采用生成结果均按3000ms入时间线，加载失败不可批准。');
} finally { await browser.close(); }
