// 独立数据服务上的真实 App 集成回归；响应延迟/错误和参考素材使用确定性替身。
import { createRequire } from 'node:module';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch({ headless: true, ...(process.env.TEST_BROWSER_PATH ? { executablePath: process.env.TEST_BROWSER_PATH } : {}) });
const page = await browser.newPage();
const errors = [];
page.on('pageerror', error => errors.push(error.message));
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  const projects = await page.evaluate(async () => {
    const result = [];
    for (const name of ['审查 A', '审查 B', '审查 C']) {
      const response = await fetch('/api/v1/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
      result.push(await response.json());
    }
    localStorage.setItem('canvas-last-project', result[0].id);
    return result;
  });
  const [a, b, c] = projects;
  await page.reload();
  const select = page.getByLabel('当前项目', { exact: true });
  await expect(select).toHaveValue(a.id);
  await page.getByRole('button', { name: '添加故事节点', exact: true }).click();
  await page.getByRole('textbox', { name: '故事内容', exact: true }).fill('保留未保存的故事');
  // 首先模拟保存失败，项目和编辑状态必须能恢复。
  await page.route(`**/api/v1/canvases/${a.id}`, route => route.request().method() === 'PUT'
    ? route.fulfill({ status: 503, json: { message: '审查保存失败' } }) : route.continue());
  await select.selectOption(b.id);
  await expect(page.getByRole('status')).toContainText('审查保存失败');
  await expect(select).toHaveValue(a.id);
  await expect(page.getByRole('textbox', { name: '故事内容', exact: true })).toHaveValue('保留未保存的故事');
  await page.unroute(`**/api/v1/canvases/${a.id}`);
  // 最新加载失败恢复上一个项目。
  await page.route(`**/api/v1/projects/${b.id}`, route => route.fulfill({ status: 503, json: { message: '审查加载失败' } }));
  await select.selectOption(b.id);
  await expect(page.getByRole('status')).toContainText('审查加载失败');
  await expect(select).toHaveValue(a.id);
  await page.unroute(`**/api/v1/projects/${b.id}`);
  // 保持 B 请求悬挂，检查工作区不可编辑，然后先提交 C，再释放 B。
  let release, entered;
  const held = new Promise(resolve => { release = resolve; });
  const seen = new Promise(resolve => { entered = resolve; });
  await page.route(`**/api/v1/projects/${b.id}`, async route => { entered(); await held; await route.continue(); });
  await select.selectOption(b.id); await seen;
  await expect(page.locator('.workspace')).toHaveAttribute('inert', '');
  await page.locator('body').click({ position: { x: 1, y: 1 } });
  await page.keyboard.press('Control+d');
  await expect(page.locator('.studio-node')).toHaveCount(1);
  await select.selectOption(c.id); await expect(select).toHaveValue(c.id);
  const oldResponse = page.waitForResponse(response => response.url().endsWith(`/projects/${b.id}`));
  release(); await oldResponse;
  await page.waitForTimeout(150);
  await expect(select).toHaveValue(c.id);
  await expect(page.locator('.studio-node')).toHaveCount(0);
  await page.unroute(`**/api/v1/projects/${b.id}`);

  // Hold responses until after a real project switch (including A -> B -> A).
  async function hold(pattern, payload, inspect = () => {}, once = false) {
    let release, entered;
    const gate = new Promise(resolve => { release = resolve; });
    const seen = new Promise(resolve => { entered = resolve; });
    let count = 0;
    await page.route(pattern, async route => {
      if (once && count) { await route.continue(); return; }
      count++; inspect(route.request()); entered(); await gate;
      await route.fulfill({ json: payload });
    });
    return { seen, count: () => count, async finish() {
      const response = page.waitForResponse(r => r.url().includes(pattern.replaceAll('**', '')));
      release(); await response; await page.waitForTimeout(200);
    }, async remove() { await page.unroute(pattern); } };
  }
  async function switchTo(id) { await select.selectOption(id); await expect(select).toHaveValue(id); }
  for (const returnToOrigin of [false, true]) {
    await switchTo(a.id);
    const originalCount = await page.locator('.studio-node').count();
    const template = await hold(`**/api/v1/projects/${a.id}/template`, { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 }, version: 987 });
    await page.locator('input[type=file][accept="application/json,.json"]').setInputFiles({ name: 'audit.json', mimeType: 'application/json', buffer: Buffer.from('{}') });
    await template.seen; await switchTo(b.id);
    if (returnToOrigin) await switchTo(a.id);
    if (!returnToOrigin) await page.getByRole('button', { name: '添加故事节点', exact: true }).click();
    await template.finish();
    await expect(select).toHaveValue(returnToOrigin ? a.id : b.id);
    await expect(page.locator('.studio-node')).toHaveCount(returnToOrigin ? originalCount : 1);
    await template.remove();

    await switchTo(a.id);
    const upload = await hold('**/api/v1/assets/import', { id: 'stale-upload', projectId: a.id, name: 'stale-upload', mime: 'audio/wav', sha256: '0'.repeat(64) }, request => expect(request.postData()).toContain(a.id));
    await page.locator('input[type=file][multiple]').setInputFiles(['first.wav', 'second.wav'].map(name => ({ name, mimeType: 'audio/wav', buffer: Buffer.from('fixture') })));
    await upload.seen; await switchTo(b.id); if (returnToOrigin) await switchTo(a.id);
    await upload.finish(); expect(upload.count()).toBe(1);
    await page.getByRole('button', { name: '素材', exact: true }).click();
    await expect(page.getByText('stale-upload', { exact: true })).toHaveCount(0);
    await upload.remove(); await page.getByRole('button', { name: '节点', exact: true }).click();

    await switchTo(a.id);
    const settings = await hold(`**/api/v1/projects/${a.id}/settings`, { ...a, settings: { ...a.settings, cloudEnabled: true } });
    await page.locator('.provider-status input[type=checkbox]').click();
    await settings.seen; await switchTo(b.id); if (returnToOrigin) await switchTo(a.id);
    await settings.finish();
    await expect(select).toHaveValue(returnToOrigin ? a.id : b.id);
    await expect(page.locator('.provider-status input[type=checkbox]')).not.toBeChecked(); await settings.remove();

    const timelinePattern = `**/api/v1/projects/${a.id}/timeline`;
    await page.route(timelinePattern, route => route.request().method() === 'GET' ? route.fulfill({ json: { clips: [{ id: 'clip', assetId: 'fixture', durationMs: 1000, inMs: 0, approved: true }], audio: [], subtitles: [], fps: 30, width: 1080, height: 1920, version: 1 } }) : route.continue());
    await switchTo(b.id); await switchTo(a.id);
    const job = { id: 'stale-export', projectId: a.id, status: 'queued' };
    const submit = await hold('**/api/v1/exports', job, request => expect(request.postDataJSON().projectId).toBe(a.id));
    await page.getByRole('button', { name: '导出 MP4', exact: true }).click();
    await submit.seen; await switchTo(b.id); if (returnToOrigin) await switchTo(a.id);
    await submit.finish(); await expect(page.locator('.export-info')).toHaveCount(0); await submit.remove();

    await switchTo(b.id); await switchTo(a.id);
    await page.route('**/api/v1/exports', route => route.fulfill({ json: job }));
    const polling = await hold('**/api/v1/exports/stale-export', { ...job, status: 'completed' });
    await page.getByRole('button', { name: '导出 MP4', exact: true }).click();
    await polling.seen; await switchTo(b.id); if (returnToOrigin) await switchTo(a.id);
    await polling.finish(); await expect(page.locator('.export-info')).toHaveCount(0);
    await polling.remove(); await page.unroute('**/api/v1/exports'); await page.unroute(timelinePattern);
  }
  await switchTo(c.id);

  for (const returnToOrigin of [false, true]) {
    for (const operation of ['save', 'restore']) {
      await switchTo(b.id); await switchTo(a.id);
      await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
      await expect(page.getByRole('button', { name: '保存设置', exact: true })).toBeEnabled();
      const pattern = `**/api/v1/projects/${a.id}${operation === 'save' ? '/settings' : ''}`;
      const stale = await hold(pattern, { ...a, name: '过期设置项目', settings: { ...a.settings, budget: { limit: '999', currency: 'CNY' } } }, () => {}, true);
      await page.getByRole('button', { name: operation === 'save' ? '保存设置' : '恢复已保存设置', exact: true }).click();
      await stale.seen;
      await page.getByRole('button', { name: '关闭设置', exact: true }).click();
      await switchTo(b.id);
      if (returnToOrigin) await switchTo(a.id);
      await stale.finish();
      await stale.remove();
      await expect(select).toHaveValue(returnToOrigin ? a.id : b.id);
      await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
      await page.getByRole('button', { name: '费用与并发', exact: true }).click();
      await expect(page.getByRole('spinbutton', { name: '项目预算上限', exact: true })).not.toHaveValue('999');
      await page.getByRole('button', { name: '关闭设置', exact: true }).click();
    }
  }
  await switchTo(c.id);

  // 直接导入一份无云调用的分镜结果；通过真实 Inspector 确认按钮检查 App 收集逻辑。
  const shot = { visualPrompt: '两人站在室内', durationMs: 5000, characterRefs: [{ id: 'p1', revisionId: 'i1' }, { id: 'p2', revisionId: 'i2' }], locationRef: { id: 'l1', revisionId: 'i3' } };
  const assets = ['i1', 'i1-extra', 'i2', 'i3', 'audio'].map(id => ({ id, revisionId: id, projectId: c.id, name: id, mime: id === 'audio' ? 'audio/wav' : 'image/png', sha256: '0'.repeat(64), createdAt: 1 }));
  const people = { characters: [{ id: 'p1', name: '甲', description: '', assetId: 'i1', referenceIds: ['i1-extra', 'audio', 'deleted'] }, { id: 'p2', name: '乙', description: '', assetId: 'i2' }], locations: [{ id: 'l1', name: '室内', description: '', assetId: 'i3' }], shots: [], version: 1 };
  await page.route(`**/api/v1/projects/${c.id}/assets`, route => route.fulfill({ json: assets }));
  await page.route(`**/api/v1/projects/${c.id}/people`, route => route.request().method() === 'GET' ? route.fulfill({ json: people }) : route.continue());
  await page.route(`**/api/v1/projects/${c.id}/tasks`, route => route.fulfill({ json: [{ id: 'fixture', node_id: 'extract', status: 'completed', created_at: 1, snapshot: { config: {}, kind: 'shots.extract' }, output: { text: '待确认分镜', shots: [shot] } }] }));
  await page.evaluate(async id => {
    const canvas = await (await fetch(`/api/v1/canvases/${id}`)).json();
    canvas.nodes = [{ id: 'extract', type: 'studio', position: { x: 20, y: 20 }, data: { kind: 'shots.extract', title: '审查分镜结果', config: {} } }];
    await fetch(`/api/v1/canvases/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': String(canvas.version) }, body: JSON.stringify(canvas) });
  }, c.id);
  await page.reload();
  await page.locator('.studio-node').click();
  await page.getByRole('button', { name: '确认分镜并加入画布', exact: true }).click();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  const references = await page.evaluate(async id => (await (await fetch(`/api/v1/canvases/${id}`)).json()).nodes.find(node => node.data.kind === 'image.generate').data.config.referenceIds, c.id);
  expect(references).toEqual(['i1', 'i1-extra', 'i2', 'i3']);
  expect(errors).toEqual([]);
  console.log('PASS: 保存失败恢复、加载失败恢复、切换禁止编辑、逆序响应、真实分镜确认的多参考图片顺序/去重/删除与 MIME 过滤；未调用云端。');
} finally { await browser.close(); }
