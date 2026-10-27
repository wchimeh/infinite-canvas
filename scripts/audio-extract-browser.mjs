import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const sample = '.runtime/audio-extract-sample.mp4';
const ffmpeg = process.env.FFMPEG_DIR ? join(process.env.FFMPEG_DIR, 'ffmpeg.exe') : 'ffmpeg';
const result = spawnSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=white:s=160x120:r=25', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '1', '-c:a', 'aac', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', sample]);
if (result.status !== 0) throw new Error(`fixture failed: ${result.stderr}`);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = []; page.on('pageerror', e => errors.push(e.message));
async function connect(source, target, output, input) {
  const a = await page.locator(`.react-flow__node[data-id="${source}"] .source[data-handleid="${output}"]`).boundingBox();
  const b = await page.locator(`.react-flow__node[data-id="${target}"] .target[data-handleid="${input}"]`).boundingBox();
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2); await page.mouse.down();
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 20 }); await page.mouse.up();
}
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async bytes => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '本地提取音频验收' }))).json();
    const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([new Uint8Array(bytes)], { type: 'video/mp4' }), '带声音的视频.mp4');
    const asset = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'source', type: 'studio', position: { x: 0, y: 0 }, data: { kind: 'asset.video', title: '视频素材', config: { assetId: asset.id } } },
      { id: 'video', type: 'studio', position: { x: 800, y: 0 }, data: { kind: 'video.image_to_video', title: '下游视频', config: {} } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('seed failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  }, [...await readFile(sample)]);
  await page.reload();
  await page.locator('.toolbox-node').filter({ hasText: '提取视频音频' }).click();
  await expect(page.locator('.inspector')).toContainText('不产生生成费用');
  await expect(page.locator('.inspector textarea')).toHaveCount(0);
  await expect(page.getByLabel('生成服务', { exact: true })).toHaveCount(0);
  const extract = page.locator('.react-flow__node.selected');
  const id = await extract.getAttribute('data-id');
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await connect('source', id, 'video', 'video');
  await page.getByRole('button', { name: '提取音频', exact: true }).click();
  await expect(extract.locator('audio')).toBeVisible({ timeout: 20000 });
  await expect.poll(() => extract.locator('audio').evaluate(a => a.readyState)).toBeGreaterThanOrEqual(1);
  await expect(extract.locator('footer')).toContainText('已完成');
  await connect(id, 'video', 'audio', 'audio');
  await expect(page.locator('.react-flow__node[data-id="video"] .target[data-handleid="audio2"]')).toBeVisible();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const evidence = await page.evaluate(async ({ pid, id }) => {
    const tasks = await (await fetch(`/api/v1/projects/${pid}/tasks`)).json();
    const task = tasks.find(t => t.node_id === id);
    const project = await (await fetch(`/api/v1/projects/${pid}`)).json();
    const canvas = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    return { status: task.status, submitted: task.submitted, external: task.external_id, local: task.snapshot.quote.basis, cloud: project.settings.cloudEnabled, connected: canvas.edges.some(e => e.source === id && e.target === 'video' && e.targetHandle === 'audio') };
  }, { pid, id });
  expect(evidence.status).toBe('completed'); expect(evidence.submitted).toBeFalsy(); expect(evidence.external).toBeFalsy();
  expect(evidence.local).toBe('local'); expect(evidence.cloud).toBeFalsy(); expect(evidence.connected).toBe(true);
  expect(errors).toEqual([]);
  console.log('PASS: 菜单添加、真实视频连线、本地提取WAV、音频预览、下游音频连接；云端关闭、未提交生成接口、零费用。');
} finally { await browser.close(); }
