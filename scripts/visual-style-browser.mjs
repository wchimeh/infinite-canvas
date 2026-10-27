import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
let submissions = 0;
await page.route('**/api/v1/runs/estimate', route => route.fulfill({ json: { nodeIds: [], totals: {}, unknownCount: 0, quotes: [] } }));
await page.route('**/api/v1/runs', route => { submissions++; return route.fulfill({ json: { id: 'qa-style-run' } }); });
await page.route('**/api/v1/runs/qa-style-run', route => route.fulfill({ json: { tasks: [] } }));
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '风格隔离验收' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = ['story.prompt', 'script.expand', 'character.extract', 'location.extract', 'shots.extract', 'shots.select', 'prompt.video_expand', 'image.character', 'image.location', 'image.generate', 'video.image_to_video'].map((kind, i) => ({ id: kind, type: 'studio', position: { x: i % 4 * 340, y: Math.floor(i / 4) * 330 }, data: { kind, title: kind, config: { prompt: 'test' } } }));
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('fixture failed');
    localStorage.setItem('canvas-last-project', p.id);
    return p.id;
  });
  await page.route(`**/api/v1/projects/${pid}/tasks`, route => route.fulfill({ json: ['character', 'location'].map(kind => ({
    id: `qa-${kind}`, node_id: `${kind}.extract`, status: 'completed', created_at: 1,
    snapshot: { kind: `${kind}.extract`, config: { visualStyle: 'anime' } },
    output: kind === 'character' ? { characters: [{ name: '演员', description: '成年人' }] } : { locations: [{ name: '街道', description: '清晨街道' }] },
  })) }));
  await page.reload();
  await expect(page.locator('.app-shell')).toBeVisible();
  await page.locator('.react-flow__controls-fitview').click();
  const select = async id => {
    await page.waitForTimeout(400); // Fit-view animates node positions.
    await page.locator(`.react-flow__node[data-id="${id}"] header`).click({ position: { x: 20, y: 12 } });
  };
  for (const kind of ['story.prompt', 'script.expand', 'character.extract', 'location.extract', 'shots.extract', 'shots.select', 'prompt.video_expand', 'image.character', 'image.location', 'image.generate', 'video.image_to_video']) {
    await select(kind);
    await expect(page.getByLabel('画面风格', { exact: true })).toBeVisible();
    await page.getByLabel('画面风格', { exact: true }).selectOption('live_action');
  }
  await select('character.extract');
  await page.getByRole('button', { name: '确认角色并创建形象节点', exact: true }).click();
  await page.locator('.react-flow__controls-fitview').click();
  await select('location.extract');
  await page.getByRole('button', { name: '确认场景并创建四视图节点', exact: true }).click();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(async () => page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    return c.nodes.filter(n => n.data.config.visualStyle === 'live_action').length;
  }, pid)).toBe(13);
  // Existing generated nodes still carry the old style; batch must update them.
  await page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    for (const n of c.nodes) if (n.data.config.characterId || n.data.config.locationId) n.data.config.visualStyle = 'anime';
    const response = await fetch(`/api/v1/canvases/${pid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(c.version) }, body: JSON.stringify(c) });
    if (!response.ok) throw new Error('batch fixture failed');
  }, pid);
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click();
  for (const [kind, label] of [['character', '角色'], ['location', '场景']]) {
    await select(`${kind}.extract`);
    await page.getByRole('button', { name: `生成全部${label}（1）`, exact: true }).click();
    await expect(page.getByRole('button', { name: `生成全部${label}（1）`, exact: true })).toBeEnabled();
  }
  await expect.poll(() => submissions).toBe(2);
  await expect.poll(async () => page.evaluate(async pid => {
    const c = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    return c.nodes.filter(n => n.data.config.visualStyle === 'live_action').length;
  }, pid)).toBe(13);
  await page.reload();
  await page.locator('.react-flow__controls-fitview').click();
  await select('script.expand');
  await expect(page.getByLabel('画面风格', { exact: true })).toHaveValue('live_action');
  expect(errors).toEqual([]);
  console.log('PASS: 11种节点风格选择、刷新持久化、旧动漫任务改为真人后确认建图及批量更新均保留真人；生成接口全部模拟。');
} finally {
  await browser.close();
}
