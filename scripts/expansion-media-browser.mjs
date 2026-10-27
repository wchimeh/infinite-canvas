import { createRequire } from 'node:module';
import { mkdir, readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url, dataDir } = await requireQaSession();
const ffmpeg = path.join(process.env.FFMPEG_DIR, 'ffmpeg.exe');
const audio = path.join(dataDir, 'ref.wav'), video = path.join(dataDir, 'ref.mp4');
execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '1', audio], { windowsHide: true });
execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=25', '-t', '1', '-c:v', 'libx264', video], { windowsHide: true });
const media = await Promise.all([audio, video].map(async p => ({ name: path.basename(p), bytes: (await readFile(p)).toString('base64') })));
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/runs', route => route.abort());
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async media => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Expansion multimedia QA' }))).json();
    const nodes = [], edges = [];
    for (const [i, item] of media.entries()) {
      const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([Uint8Array.from(atob(item.bytes), c => c.charCodeAt(0))]), item.name);
      const a = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
      const port = i ? 'video' : 'audio';
      nodes.push({ id: port, type: 'studio', position: { x: 0, y: i * 400 }, data: { kind: 'asset.' + port, title: port, config: { assetId: a.id } } });
      edges.push({ id: port, source: port, target: 'expand', sourceHandle: port, targetHandle: port });
    }
    nodes.push({ id: 'expand', type: 'studio', position: { x: 400, y: 100 }, data: { kind: 'prompt.video_expand', title: 'Expand QA', config: { prompt: 'Describe references' } } });
    nodes.push({ id: 'generate', type: 'studio', position: { x: 800, y: 100 }, data: { kind: 'video.image_to_video', title: 'Video QA', config: { prompt: 'scene' } } });
    nodes.push({ id: 'fresh-expand', type: 'studio', position: { x: 400, y: 600 }, data: { kind: 'prompt.video_expand', title: 'New Expand QA', config: {} } });
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    const req = opts('PUT', { ...c, nodes, edges }); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture save failed');
    localStorage.setItem('canvas-last-project', p.id);
  }, media);
  await page.reload(); await page.locator('.react-flow__controls-fitview').click();
  const target = page.locator('[data-id="expand"]');
  await target.locator('header').click();
  await expect(target.locator('.target[data-handleid="video2"]')).toBeVisible();
  await expect(target.locator('.target[data-handleid="audio2"]')).toHaveCount(0);
  await expect(target.getByText('旧音频（不参与扩写）')).toBeVisible();
  await expect(target.locator('.target[data-handleid="audio"]')).not.toHaveClass(/connectablestart/);
  await expect(page.locator('[data-id="fresh-expand"] .target[data-handleid^="audio"]')).toHaveCount(0);
  await expect(page.locator('[data-id="generate"] .target[data-handleid="audio"]')).toBeVisible();
  await expect(page.locator('.reference-list label').filter({ hasText: 'ref.wav' })).toHaveCount(0);
  await page.locator('.reference-list label').filter({ hasText: 'ref.mp4' }).locator('input').check();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.reload(); await page.locator('.react-flow__controls-fitview').click(); await target.locator('header').click();
  await expect(target.getByText('旧音频（不参与扩写）')).toBeVisible();
  await expect(page.locator('.reference-list input:checked')).toHaveCount(1);
  await mkdir('.runtime/qa', { recursive: true }); await page.screenshot({ path: '.runtime/qa/expansion-media.png' });
  expect(errors).toEqual([]);
  console.log('PASS: visual-only expansion, ignored legacy audio, independent video audio input and persistence');
} finally { await browser.close(); }
