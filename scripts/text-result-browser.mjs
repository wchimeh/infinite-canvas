import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1050 } });
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: 'Text edit QA' }))).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = ['story.prompt', 'text.concat', 'text.concat'].map((kind, i) => ({ id: `n${i}`, type: 'studio', position: { x: i * 330, y: 0 }, data: { kind, title: `node${i}`, config: i ? {} : { prompt: 'original text' } } }));
    c.edges = [1, 2].map(i => ({ id: `e${i}`, source: `n${i - 1}`, target: `n${i}`, sourceHandle: 'text', targetHandle: 'text', data: { kind: 'data' } }));
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('save fixture failed');
    if (!(await fetch('/api/v1/runs', opts('POST', { projectId: p.id, nodeIds: ['n1'] }))).ok) throw new Error('run failed');
    localStorage.setItem('canvas-last-project', p.id);
    return p.id;
  });
  await page.reload();
  const middle = page.locator('.react-flow__node[data-id="n1"]');
  await expect(middle).toContainText('original text', { timeout: 15000 });
  await middle.locator('header').click();
  await page.getByRole('button', { name: '编辑结果', exact: true }).click();
  await page.getByLabel('编辑生成结果').fill('discard this');
  await page.getByRole('button', { name: '取消', exact: true }).click();
  await expect(middle).toContainText('original text');
  await page.getByRole('button', { name: '编辑结果', exact: true }).click();
  await page.getByLabel('编辑生成结果').fill('edited text');
  await page.getByRole('button', { name: '保存修改', exact: true }).click();
  await expect(middle).toContainText('edited text');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.reload();
  await expect(middle).toContainText('edited text');
  await page.evaluate(async pid => {
    const r = await fetch('/api/v1/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ projectId: pid, nodeIds: ['n2'] }) });
    if (!r.ok) throw new Error('downstream failed');
  }, pid);
  await expect(page.locator('.react-flow__node[data-id="n2"]')).toContainText('edited text', { timeout: 15000 });
  await middle.locator('header').click();
  await page.getByRole('button', { name: '恢复生成结果', exact: true }).click();
  await expect(middle).toContainText('original text');
  await expect(page.getByRole('button', { name: '恢复生成结果', exact: true })).toHaveCount(0);
  console.log('PASS: edit, cancel, persist/reopen, downstream execution, restore; local only');
} finally { await browser.close(); }
