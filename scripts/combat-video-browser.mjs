import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1100 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.route('**/api/v1/runs', route => route.abort());
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  await page.evaluate(async () => {
    const response = await fetch('/api/v1/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'Combat video QA' }) });
    const project = await response.json(); localStorage.setItem('canvas-last-project', project.id);
  });
  await page.reload();
  await page.locator('.toolbox-node').filter({ hasText: '生成视频-武打' }).click();
  const inspector = page.locator('.inspector'), field = name => inspector.getByLabel(name, { exact: true });
  await expect(field('生成工作流')).toHaveValue('builtin-minimax-h3-combat');
  for (const [name, value] of [['生成时长（秒）', '8'], ['武打分辨率（MP）', '0.5'], ['武打采样步数', '6'], ['提示词引导（CFG）', '1'], ['武打强度', '0.35'], ['速度强度', '1']]) {
    await expect(field(name)).toHaveValue(value);
  }
  const target = page.locator('.react-flow__node').filter({ hasText: '生成视频-武打' });
  for (const port of ['image', 'audio', 'video']) await expect(target.locator(`.target[data-handleid="${port}"]`)).toHaveCount(1);
  await expect(target.locator('.target[data-handleid^="videoAudio"]')).toHaveCount(0);
  await field('武打画面比例').selectOption('9:16 (Portrait Widescreen)');
  for (const [name, value] of [['生成时长（秒）', '12'], ['武打分辨率（MP）', '0.8'], ['武打采样步数', '16'], ['提示词引导（CFG）', '2'], ['武打强度', '0.9'], ['动作修复强度', '0.2'], ['动作连贯强度', '0.6'], ['速度强度', '3']]) {
    await field(name).fill(value); await field(name).press('Tab');
  }
  await field('武打种子模式').selectOption('fixed');
  await field('武打固定种子').fill('123'); await field('武打固定种子').press('Tab');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.evaluate(async () => {
    const pid = localStorage.getItem('canvas-last-project');
    const canvas = await (await fetch(`/api/v1/canvases/${pid}`)).json();
    const node = canvas.nodes.find(n => n.data.kind === 'video.combat');
    node.position = { x: 450, y: 100 };
    for (const [index, type] of ['image', 'audio', 'video'].entries()) {
      const source = `source-${type}`;
      canvas.nodes.push({ id: source, type: 'studio', position: { x: 30, y: 50 + index * 280 }, data: { kind: 'asset.' + type, title: 'Reference ' + type, config: {} } });
      canvas.edges.push({ id: source, source, target: node.id, sourceHandle: type, targetHandle: type, data: { kind: 'data' } });
    }
    const response = await fetch(`/api/v1/canvases/${pid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(canvas.version) }, body: JSON.stringify(canvas) });
    if (!response.ok) throw new Error('connected fixture failed');
  });
  await page.reload(); await page.locator('.react-flow__controls-fitview').click();
  await target.locator('header').click();
  for (const port of ['image', 'audio', 'video']) await expect(target.locator(`.target[data-handleid="${port}2"]`)).toHaveCount(1);
  for (const [name, value] of [['生成时长（秒）', '12'], ['武打画面比例', '9:16 (Portrait Widescreen)'], ['武打采样步数', '16'], ['武打强度', '0.9'], ['武打固定种子', '123']]) await expect(field(name)).toHaveValue(value);
  await field('武打强度').scrollIntoViewIfNeeded();
  await mkdir('.runtime/qa', { recursive: true }); await page.screenshot({ path: '.runtime/qa/combat-video.png' });
  expect(errors).toEqual([]);
  console.log('PASS: combat node creation, workflow defaults, dynamic media ports, parameters and persistence');
} finally { await browser.close(); }
