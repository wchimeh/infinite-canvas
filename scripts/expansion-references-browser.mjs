import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
await page.route('**/api/v1/runs', route => route.abort());
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '扩写多图验收' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = ['asset.image', 'asset.image', 'prompt.video_expand'].map((kind, i) => ({ id: `n${i}`, type: 'studio', position: { x: i === 2 ? 430 : 40, y: i === 1 ? 320 : 0 }, data: { kind, title: `node${i}`, config: {} } }));
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
  });
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click();
  await page.waitForTimeout(400);
  const target = page.locator('.react-flow__node[data-id="n2"]');
  await expect(target.locator('.react-flow__handle.target')).toHaveCount(2);
  for (let i = 0; i < 2; i++) {
    const source = await page.locator(`.react-flow__node[data-id="n${i}"] .react-flow__handle.source`).boundingBox();
    const dest = await target.locator(`.react-flow__handle.target[data-handleid="${i ? 'image2' : 'image'}"]`).boundingBox();
    await page.mouse.move(source.x + source.width / 2, source.y + source.height / 2);
    await page.mouse.down();
    await page.mouse.move(dest.x + dest.width / 2, dest.y + dest.height / 2, { steps: 20 });
    await page.mouse.up();
    await expect(target.locator('.react-flow__handle.target')).toHaveCount(i + 3);
  }
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);
  console.log('PASS: 扩写节点连续接入两图并自动展开参考图2、3；未调用生成。');
} finally { await browser.close(); }
