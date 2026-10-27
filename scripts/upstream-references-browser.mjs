import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
await page.route('**/api/v1/runs', route => route.abort());
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Auto reference wires QA' }))).json();
    const image = document.createElement('canvas'); image.width = 24; image.height = 24;
    const blob = await new Promise(resolve => image.toBlob(resolve));
    const ids = [];
    for (let i = 0; i < 2; i++) {
      const body = new FormData(); body.set('projectId', p.id); body.set('file', blob, `reference-${i}.png`);
      ids.push((await (await fetch('/api/v1/assets/import', { method: 'POST', body })).json()).id);
    }
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [
      { id: 'image', type: 'studio', position: { x: 0, y: 0 }, data: { kind: 'asset.image', title: 'Image', config: { assetId: ids[0] } } },
      { id: 'up', type: 'studio', position: { x: 340, y: 0 }, data: { kind: 'prompt.video_expand', title: 'Upstream', config: { referenceIds: [ids[1]] } } },
      { id: 'video', type: 'studio', position: { x: 680, y: 0 }, data: { kind: 'video.image_to_video', title: 'Video', config: { referenceIds: [ids[0]] } } },
    ];
    c.edges = [{ id: 'image-up', source: 'image', target: 'up', sourceHandle: 'image', targetHandle: 'image', data: { kind: 'data' } }, { id: 'up-video', source: 'up', target: 'video', sourceHandle: 'text', targetHandle: 'text', data: { kind: 'data' } }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id); return p.id;
  });
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await page.locator('.react-flow__node[data-id="video"] header').click();
  await page.getByRole('button', { name: '连接上游参考图', exact: true }).click();
  await expect(page.getByText('已连接 2 张上游参考图，可撤销本次操作', { exact: true })).toBeVisible();
  await expect(page.locator('.react-flow__edge')).toHaveCount(4);
  await expect(page.locator('.react-flow__node[data-id="video"] .target[data-handleid^="image"]')).toHaveCount(3);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);
  await page.getByRole('button', { name: '重做', exact: true }).click();
  await expect(page.locator('.react-flow__edge')).toHaveCount(4);
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const images = c.edges.filter(e => e.target === 'video' && e.targetHandle.startsWith('image'));
    if (images.length !== 2 || images[0].source !== 'image' || images[1].targetHandle !== 'image2') throw new Error('Wrong reference order');
    if (c.nodes.find(n => n.id === 'video').data.config.referenceIds.length) throw new Error('Images included twice');
    if (c.nodes.length !== 4) throw new Error('Expected one new asset node');
  }, pid);
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click(); await page.waitForTimeout(400);
  await expect(page.locator('.react-flow__edge')).toHaveCount(4);
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/upstream-reference-wires.png' });
  console.log('PASS: click creates wires and asset node, dynamic next port, one-step undo/redo, persistence');
} finally { await browser.close(); }
