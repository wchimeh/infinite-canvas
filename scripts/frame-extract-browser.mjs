import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url, dataDir } = await requireQaSession();
const sample = join(dataDir, 'frame-sample.mp4');
execFileSync(join(process.env.FFMPEG_DIR, 'ffmpeg.exe'), ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=160x120:r=10:d=3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', sample], { windowsHide: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1100 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async bytes => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '截帧验收' }))).json();
    const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([new Uint8Array(bytes)], { type: 'video/mp4' }), 'source.mp4');
    const asset = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [{ id: 'source', type: 'studio', position: { x: 0, y: 0 }, data: { kind: 'asset.video', title: '视频', config: { assetId: asset.id } } },
      { id: 'downstream', type: 'studio', position: { x: 700, y: 0 }, data: { kind: 'image.prop', title: '下游图片', config: {} } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  }, [...await readFile(sample)]);
  await page.reload();
  await expect(page.locator('.app-shell')).toBeVisible();
  await page.locator('.toolbox-node').filter({ hasText: '提取视频帧' }).click();
  const target = page.locator('.react-flow__node.selected');
  const id = await target.getAttribute('data-id');
  await expect(page.getByText('请将视频素材或生成视频节点的输出连接到此节点。', { exact: true })).toBeVisible();
  await expect(page.getByLabel('生成服务', { exact: true })).toHaveCount(0);
  async function connect(source, dest, output, input) {
    await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(350);
    const a = await page.locator(`.react-flow__node[data-id="${source}"] .source[data-handleid="${output}"]`).boundingBox();
    const b = await page.locator(`.react-flow__node[data-id="${dest}"] .target[data-handleid="${input}"]`).boundingBox();
    await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2); await page.mouse.down();
    await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 20 }); await page.mouse.up();
  }
  await connect('source', id, 'video', 'video');
  const preview = page.getByLabel('截帧视频预览', { exact: true });
  await expect.poll(() => preview.evaluate(v => v.readyState)).toBeGreaterThanOrEqual(2);
  const slider = page.getByLabel('截帧进度', { exact: true });
  const box = await slider.boundingBox();
  await page.mouse.move(box.x + 5, box.y + box.height / 2); await page.mouse.down();
  await page.mouse.move(box.x + box.width * .55, box.y + box.height / 2, { steps: 10 }); await page.mouse.up();
  const chosen = Number(await page.getByLabel('截帧时间（秒）', { exact: true }).inputValue());
  expect(chosen).toBeGreaterThan(1); expect(chosen).toBeLessThan(2);
  await expect.poll(() => preview.evaluate(v => v.currentTime)).toBeCloseTo(chosen, 2);
  await page.getByRole('button', { name: '截取当前帧', exact: true }).click();
  const node = page.locator(`.react-flow__node[data-id="${id}"]`);
  await expect(node.locator('img')).toBeVisible({ timeout: 30000 });
  await expect(node.locator('footer')).toContainText('已完成');
  await connect(id, 'downstream', 'image', 'image');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const evidence = await page.evaluate(async ({ pid, id }) => {
    const tasks = await (await fetch(`/api/v1/projects/${pid}/tasks`)).json();
    const t = tasks.find(t => t.node_id === id);
    return { submitted: t.submitted, local: t.snapshot.quote.basis, time: t.snapshot.config.frameTime };
  }, { pid, id });
  expect(evidence.submitted).toBeFalsy(); expect(evidence.local).toBe('local'); expect(evidence.time).toBe(chosen);
  await page.reload(); await node.locator('header').click();
  await expect(page.getByLabel('截帧时间（秒）', { exact: true })).toHaveValue(String(chosen));
  await expect.poll(() => preview.evaluate(v => v.currentTime)).toBeCloseTo(chosen, 2);
  const oldImage = await node.locator('img').getAttribute('src');
  await page.locator('.candidates').getByRole('button', { name: '采用', exact: true }).click();
  await page.getByLabel('截帧时间（秒）', { exact: true }).fill('0');
  await page.getByRole('button', { name: '截取当前帧', exact: true }).click();
  await expect(node.locator('footer')).toContainText('已完成', { timeout: 30000 });
  await expect(node.locator('img')).not.toHaveAttribute('src', oldImage);
  await expect(page.locator('.candidate')).toHaveCount(2);
  expect(errors).toEqual([]);
  console.log('PASS: video connection, slider seek, local PNG extraction, downstream image connection, saved time and reload');
} finally { await browser.close(); }
