// 独立 Chromium 验收，不连接用户的浏览器或登录资料。
import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps/desktop/package.json'));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || path.join(root, '.runtime/session.json'), 'utf8'));
await mkdir(path.join(root, '.runtime/qa'), { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.TEST_BROWSER_PATH ? { executablePath: process.env.TEST_BROWSER_PATH } : {}) });
const page = await browser.newPage({ viewport: { width: 1500, height: 960 } });
const errors = [];
let savedGenerationProfiles;
page.on('pageerror', error => errors.push(error.message));
const node = title => page.locator('.react-flow__node').filter({ has: page.locator('header strong', { hasText: title }) });
async function fitCanvas() {
  await page.locator('.react-flow__controls-fitview').click();
  // 等待 fitView 动画结束后再读取端口屏幕坐标。
  await page.waitForTimeout(350);
}
async function connect(source, output, target, input) {
  const start = await source.locator(`.react-flow__handle.source[data-handleid="${output}"]`).boundingBox();
  const end = await target.locator(`.react-flow__handle.target[data-handleid="${input}"]`).boundingBox();
  if (!start || !end) throw new Error('节点端口不可见，无法执行实际拖线');
  await page.mouse.move(start.x + start.width / 2, start.y + start.height / 2);
  await page.mouse.down();
  await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2, { steps: 20 });
  await page.mouse.up();
}
async function savedState() {
  return page.evaluate(async () => {
    const id = document.querySelector('[aria-label="当前项目"]').value;
    const get = async path => {
      const response = await fetch('/api/v1' + path);
      if (!response.ok) throw new Error(`验收读取失败：${response.status}`);
      return response.json();
    };
    return { canvas: await get(`/canvases/${id}`), people: await get(`/projects/${id}/people`), assets: await get(`/projects/${id}/assets`) };
  });
}
try {
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  if (!await page.getByRole('heading', { name: '新建短剧项目' }).isVisible()) {
    await page.getByRole('button', { name: '新建项目', exact: true }).click();
  }
  await page.getByLabel('项目名称').fill('自动验收 · ' + Date.now());
  await page.getByRole('button', { name: '创建项目', exact: true }).click();
  await page.getByRole('button', { name: '添加故事节点', exact: true }).click();
  await page.getByRole('textbox', { name: '故事内容', exact: true }).fill('雨夜，林夏收到一封来自十年前的信。她走向车站，发现等候她的人正是自己。');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator('.studio-node')).toHaveCount(1);
  await page.locator('.studio-node').click();
  await expect(page.getByRole('textbox', { name: '故事内容', exact: true })).toHaveValue(/雨夜/);
  await page.getByRole('button', { name: '输出故事内容', exact: true }).click();
  await expect(page.locator('.studio-node footer')).toContainText('已完成', { timeout: 15000 });
  await expect(page.locator('.task-filters')).toBeVisible();
  await page.getByRole('button', { name: '时间线', exact: true }).click();
  await page.getByRole('button', { name: '复制选中节点', exact: true }).click();
  await expect(page.locator('.studio-node')).toHaveCount(2);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await expect(page.locator('.studio-node')).toHaveCount(1);
  await page.getByRole('button', { name: '重做', exact: true }).click();
  await expect(page.locator('.studio-node')).toHaveCount(2);
  await page.getByRole('button', { name: '删除选中对象', exact: true }).click();
  await expect(page.locator('.studio-node')).toHaveCount(1);
  await page.getByRole('button', { name: '角色 / 场景', exact: true }).click();
  await page.getByRole('button', { name: '添加角色', exact: true }).click();
  await page.locator('.dialog').getByLabel('名称', { exact: true }).fill('林夏');
  await page.locator('.dialog').getByLabel('描述', { exact: true }).fill('短发、深蓝风衣，手持旧信封。');
  await page.getByRole('button', { name: '保存设定', exact: true }).click();
  await expect(page.locator('.profile-card')).toContainText('林夏');
  await page.getByRole('button', { name: '节点', exact: true }).click();
  await page.getByRole('button', { name: '生成分镜图', exact: true }).click();
  await page.getByLabel('提示词', { exact: true }).fill('雨夜车站，电影分镜，蓝色灯光');
  await page.getByRole('button', { name: '运行节点', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('仅本地模式');
  await page.getByRole('button', { name: '关闭提示', exact: true }).click();
  await fitCanvas();
  await connect(node('故事 / 文本'), 'text', node('生成分镜图'), 'text');
  await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  await connect(node('故事 / 文本'), 'text', node('生成分镜图'), 'image');
  await expect(page.getByRole('status')).toContainText('端口类型不匹配');
  await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  await page.getByRole('button', { name: '关闭提示', exact: true }).click();

  // 用浏览器 Canvas 创建真实 PNG，再通过文件输入执行真实导入。
  const png = await page.evaluate(() => {
    const canvas = document.createElement('canvas'); canvas.width = 32; canvas.height = 32;
    const context = canvas.getContext('2d'); context.fillStyle = '#78b7df'; context.fillRect(0, 0, 32, 32);
    return canvas.toDataURL('image/png').split(',')[1];
  });
  await page.getByRole('button', { name: '素材', exact: true }).click();
  await page.locator('input[type="file"][multiple]').setInputFiles({ name: '回归参考图.png', mimeType: 'image/png', buffer: Buffer.from(png, 'base64') });
  const imported = page.locator('.asset-item').filter({ hasText: '回归参考图.png' });
  await expect(imported).toHaveCount(1);
  await expect.poll(() => imported.locator('img').evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
  await imported.getByRole('button', { name: '加入画布', exact: true }).click();
  await fitCanvas();
  await expect.poll(() => node('回归参考图.png').locator('img').evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
  await connect(node('回归参考图.png'), 'image', node('生成分镜图'), 'image');
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);

  await page.getByRole('button', { name: '角色 / 场景', exact: true }).click();
  await page.locator('.profile-card').filter({ hasText: '林夏' }).getByRole('button', { name: '编辑', exact: true }).click();
  const referenceSelect = page.getByLabel('参考图版本', { exact: true });
  await expect(referenceSelect.locator('option')).toHaveCount(2);
  await referenceSelect.selectOption({ index: 1 });
  await page.getByRole('button', { name: '保存设定', exact: true }).click();
  await page.locator('.profile-card').filter({ hasText: '林夏' }).getByRole('button', { name: '加入画布', exact: true }).click();
  await fitCanvas();
  await expect.poll(() => node('林夏').locator('img').evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
  await connect(node('林夏'), 'image', node('生成分镜图'), 'image');
  await expect(page.locator('.react-flow__edge')).toHaveCount(2);

  await page.getByRole('button', { name: '节点', exact: true }).click();
  await page.getByRole('button', { name: '参考图创作', exact: true }).click();
  await fitCanvas();
  await connect(node('生成分镜图'), 'image', node('参考图创作'), 'image');
  await expect(page.locator('.react-flow__edge')).toHaveCount(3);
  await connect(node('参考图创作'), 'image', node('生成分镜图'), 'image');
  await expect(page.getByRole('status')).toContainText('循环依赖');
  await expect(page.locator('.react-flow__edge')).toHaveCount(3);
  await page.getByRole('button', { name: '关闭提示', exact: true }).click();

  // 修改节点位置与视口，保存后用 API 和重开后的 DOM 同时验证。
  const story = await node('故事 / 文本').locator('header').boundingBox();
  await page.mouse.move(story.x + 40, story.y + 10);
  await page.mouse.down(); await page.mouse.move(story.x + 80, story.y + 40, { steps: 10 }); await page.mouse.up();
  await page.locator('.react-flow__controls-zoomout').click();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.getByText('项目已保存', { exact: true })).toBeVisible();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');
  const before = await savedState();
  expect(before.canvas.nodes).toHaveLength(5);
  expect(before.canvas.edges).toHaveLength(3);
  expect(before.assets).toHaveLength(1);
  expect(before.people.characters[0].assetId).toBe(before.assets[0].id);
  expect(before.canvas.nodes.find(n => n.data.kind === 'character.reference').data.config.assetId).toBe(before.assets[0].id);
  await page.reload();
  await expect(page.locator('.studio-node')).toHaveCount(5);
  await expect(page.locator('.react-flow__edge')).toHaveCount(3);
  const after = await savedState();
  expect(after.canvas.nodes).toEqual(before.canvas.nodes);
  expect(after.canvas.edges).toEqual(before.canvas.edges);
  expect(after.canvas.viewport).toEqual(before.canvas.viewport);
  expect(after.people).toEqual(before.people);
  expect(after.assets).toEqual(before.assets);
  await expect.poll(async () => {
    const rendered = await page.locator('.react-flow__viewport').evaluate(el => {
      const matrix = new DOMMatrix(getComputedStyle(el).transform);
      return { x: matrix.e, y: matrix.f, zoom: matrix.a };
    });
    return Math.max(...['x', 'y', 'zoom'].map(key => Math.abs(rendered[key] - before.canvas.viewport[key])));
  }).toBeLessThan(0.001);
  await expect.poll(() => node('林夏').locator('img').evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
  await page.getByRole('button', { name: '角色 / 场景', exact: true }).click();
  await expect(page.locator('.profile-card')).toContainText('林夏');

  // 分组通过 Shift 实际多选，验证撤销/重做和持久化。
  await node('故事 / 文本').locator('header strong').click();
  await node('生成分镜图').locator('header strong').click({ modifiers: ['Shift'] });
  await page.getByRole('button', { name: '组合选中节点', exact: true }).click();
  await expect(page.locator('.canvas-group')).toHaveCount(1);
  await page.getByRole('button', { name: '撤销', exact: true }).click();
  await expect(page.locator('.canvas-group')).toHaveCount(0);
  await page.getByRole('button', { name: '重做', exact: true }).click();
  await expect(page.locator('.canvas-group')).toHaveCount(1);
  await page.getByRole('button', { name: '保存', exact: true }).click();

  await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
  await page.getByRole('button', { name: '费用与并发', exact: true }).click();
  await page.getByLabel('项目预算上限', { exact: true }).fill('20');
  await page.getByLabel('图片＋视频并发数', { exact: true }).fill('2');
  await page.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(page.locator('.settings-dialog').getByRole('status')).toContainText('设置已保存');
  const savedLimits = await page.evaluate(async () => (await (await fetch('/api/v1/settings')).json()).concurrency);
  expect(savedLimits.media).toBe(2);
  expect(savedLimits.text).toBe(1);
  await page.screenshot({ path: path.join(root, '.runtime/qa/settings.png'), fullPage: true });
  await page.getByRole('button', { name: '关闭设置', exact: true }).click();

  // 完整项目包和画布模板通过真实下载/文件选择导入。
  await page.getByText('项目工具', { exact: true }).click();
  const archiveDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: '导出完整项目', exact: true }).click();
  const archive = await archiveDownload;
  const archivePath = path.join(root, '.runtime/qa/project.canvas.zip');
  await archive.saveAs(archivePath);
  const oldProject = await page.getByLabel('当前项目', { exact: true }).inputValue();
  await page.locator('input[type="file"][accept="application/zip,.zip"]').setInputFiles(archivePath);
  await expect.poll(() => page.getByLabel('当前项目', { exact: true }).inputValue()).not.toBe(oldProject);
  await expect(page.locator('.studio-node')).toHaveCount(5);
  await expect(page.locator('.canvas-group')).toHaveCount(1);
  const importedState = await savedState();
  expect(importedState.assets[0].sha256).toBe(before.assets[0].sha256);
  expect(importedState.assets[0].id).not.toBe(before.assets[0].id);
  expect(importedState.people.characters[0].assetId).toBe(importedState.assets[0].id);
  const templateDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: '导出画布模板', exact: true }).click();
  const template = await templateDownload;
  const templatePath = path.join(root, '.runtime/qa/template.json');
  await template.saveAs(templatePath);
  await page.locator('input[type="file"][accept="application/json,.json"]').setInputFiles(templatePath);
  await expect(page.locator('.canvas-toolbar .muted')).toContainText('10 节点');
  const templated = await savedState();
  expect(templated.canvas.nodes).toHaveLength(10);
  expect(new Set(templated.canvas.nodes.map(n => n.id)).size).toBe(10);
  expect(templated.canvas.nodes.slice(5).some(n => n.data.config.assetId)).toBe(false);
  await page.getByText('项目工具', { exact: true }).click();

  // 真实媒体素材进入时间线，编辑后生成有混音/字幕的低分辨率预览。
  const env = await readFile(path.join(root, '.env'), 'utf8').catch(() => '');
  const ffmpegDir = /^FFMPEG_DIR=(.+)$/m.exec(env)?.[1].trim();
  const ffmpeg = process.env.FFMPEG_DIR ? path.join(process.env.FFMPEG_DIR, 'ffmpeg.exe') : ffmpegDir ? path.join(ffmpegDir, 'ffmpeg.exe') : 'ffmpeg';
  const videoPath = path.join(root, '.runtime/qa/timeline.mp4'), audioPath = path.join(root, '.runtime/qa/music.wav');
  execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=navy:s=320x568:r=30:d=6', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', videoPath], { windowsHide: true });
  execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=6', audioPath], { windowsHide: true });
  await page.getByRole('button', { name: '素材', exact: true }).click();
  await page.locator('input[type="file"][multiple]').setInputFiles([videoPath, audioPath]);
  const videoAsset = page.locator('.asset-item').filter({ hasText: 'timeline.mp4' });
  await expect(videoAsset).toHaveCount(1);
  await videoAsset.getByRole('button', { name: '加入画布', exact: true }).click();
  await page.getByRole('button', { name: '批准并加入时间线', exact: true }).click();
  const timelineClip = page.locator('.timeline-clip');
  await timelineClip.getByText('裁切与混音', { exact: true }).click();
  await page.getByLabel('timeline.mp4源入点', { exact: true }).fill('1');
  await page.getByLabel('timeline.mp4时长', { exact: true }).fill('2');
  await page.getByLabel('timeline.mp4音量', { exact: true }).fill('0.2');
  await page.getByLabel('timeline.mp4淡入', { exact: true }).fill('0.2');
  await page.getByLabel('添加背景音乐', { exact: true }).selectOption({ label: 'music.wav' });
  await page.locator('.audio-clip').getByText('裁切与混音', { exact: true }).click();
  await page.getByLabel('music.wav时长', { exact: true }).fill('2');
  await page.getByLabel('字幕内容', { exact: true }).fill('完整工作台验收');
  await page.getByLabel('字幕结束秒', { exact: true }).fill('2');
  await page.locator('.subtitle-entry').getByRole('button', { name: '添加', exact: true }).click();
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');
  await page.getByRole('button', { name: '合成预览', exact: true }).click();
  const composed = page.locator('.preview-dialog video');
  await expect(composed).toBeVisible({ timeout: 45000 });
  await expect.poll(() => composed.evaluate(video => video.readyState >= 1 && video.duration > 1.9 && video.duration < 2.1), { timeout: 15000 }).toBe(true);
  await page.screenshot({ path: path.join(root, '.runtime/qa/composed-preview.png'), fullPage: true });
  await page.locator('.preview-dialog').getByRole('button', { name: '关闭', exact: true }).click();
  await page.reload();
  await expect(page.locator('.timeline-clip')).toHaveCount(1);
  await expect(page.locator('.audio-clip')).toHaveCount(1);
  await expect(page.locator('.subtitle-chip')).toContainText('完整工作台验收');
  await page.screenshot({ path: path.join(root, '.runtime/qa/workspace.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(root, '.runtime/qa/mobile.png'), fullPage: true });
  // 多服务配置只保存测试地址；不运行云端任务，也不读取或修改用户密钥。
  savedGenerationProfiles = await page.evaluate(async () => {
    const settings = await (await fetch('/api/v1/settings')).json();
    return { textServices: settings.textServices, cloudWorkflows: settings.cloudWorkflows, pricing: settings.pricing };
  });
  await page.setViewportSize({ width: 1500, height: 960 });
  await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
  const dialog = page.locator('.settings-dialog');
  await dialog.getByRole('button', { name: '添加文本服务', exact: true }).click();
  await expect(dialog.getByRole('button', { name: '移除此服务配置', exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: '移除此服务配置', exact: true }).click();
  await expect(dialog.getByLabel('服务名称', { exact: true })).toHaveCount(0);
  for (const name of ['QA 文本 A', 'QA 文本 B']) {
    await dialog.getByRole('button', { name: '添加文本服务', exact: true }).click();
    await dialog.getByLabel('服务名称', { exact: true }).fill(name);
    await dialog.getByLabel('服务地址', { exact: true }).fill('https://example.invalid/v1');
    await dialog.getByLabel('模型 1', { exact: true }).fill('small');
    await dialog.getByRole('button', { name: '添加模型', exact: true }).click();
    await dialog.getByLabel('模型 2', { exact: true }).fill('large');
  }
  // 仅模拟旧凭据保存响应，确保不会把尚未保存的新服务列表重置。
  await page.route('**/api/v1/settings/credentials/runninghub', async route => {
    const persisted = await page.evaluate(async () => (await fetch('/api/v1/settings')).json());
    await route.fulfill({ json: persisted });
  });
  await dialog.getByLabel('RunningHub 密钥', { exact: true }).fill('qa-not-sent');
  await dialog.getByRole('button', { name: '保存密钥', exact: true }).first().click();
  await expect(dialog.getByText('RunningHub 凭据已保存在系统中', { exact: true })).toBeVisible();
  await expect(dialog.getByLabel('服务名称', { exact: true })).toHaveValue('QA 文本 B');
  await page.unroute('**/api/v1/settings/credentials/runninghub');
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByRole('status')).toContainText('设置已保存');
  await page.screenshot({ path: path.join(root, '.runtime/qa/text-services.png'), fullPage: true });
  // 模拟服务 B 的凭据状态，不写系统密钥；撤销不能被另一个未完成草稿阻止。
  const credentialServiceId = await page.evaluate(async () => (await (await fetch('/api/v1/settings')).json()).textServices.find(s => s.name === 'QA 文本 B').id);
  const credentialRoute = `**/api/v1/settings/credentials/text-${credentialServiceId}`;
  await page.route(credentialRoute, async route => {
    const persisted = await page.evaluate(async () => (await fetch('/api/v1/settings')).json());
    const configured = route.request().method() !== 'DELETE';
    persisted.credentials['text-' + credentialServiceId] = { configured, source: configured ? 'vault' : 'none' };
    await route.fulfill({ json: persisted });
  });
  await dialog.getByLabel('此服务的 API 密钥', { exact: true }).fill('qa-not-stored');
  await dialog.getByRole('button', { name: '保存此服务密钥', exact: true }).click();
  await expect(dialog.getByText('该服务的密钥已保存在系统中', { exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: '添加文本服务', exact: true }).click();
  await dialog.getByRole('button', { name: 'QA 文本 B 已启用', exact: true }).click();
  let settingsWritesDuringRevocation = 0;
  const observeWrite = request => { if (request.method() === 'PUT' && new URL(request.url()).pathname === '/api/v1/settings') settingsWritesDuringRevocation++; };
  page.on('request', observeWrite);
  await dialog.getByRole('button', { name: '撤销此服务密钥', exact: true }).click();
  await expect(dialog.getByText('该服务的密钥已撤销', { exact: true })).toBeVisible();
  page.off('request', observeWrite);
  expect(settingsWritesDuringRevocation).toBe(0);
  await expect(dialog.getByRole('button', { name: '撤销此服务密钥', exact: true })).toBeDisabled();
  await dialog.getByRole('button', { name: '新文本服务 已启用', exact: true }).click();
  await expect(dialog.getByLabel('服务地址', { exact: true })).toHaveValue('');
  await dialog.getByRole('button', { name: '移除此服务配置', exact: true }).click();
  await page.unroute(credentialRoute);
  await dialog.getByRole('button', { name: '云端工作流', exact: true }).click();
  await dialog.getByRole('button', { name: '添加工作流', exact: true }).click();
  await dialog.getByRole('button', { name: '移除此工作流配置', exact: true }).click();
  const workflowCount = await dialog.locator('.profile-list button').count();
  await dialog.getByLabel('导入云端工作流', { exact: true }).setInputFiles({ name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ name: '不能导入的配置', kinds: ['image.generate'], workflowId: '123', mappings: [], resultNodes: [], version: 1 })) });
  await expect(dialog.getByRole('alert')).toContainText('请配置输出节点');
  await expect(dialog.locator('.profile-list button')).toHaveCount(workflowCount);
  const fullGraph = {
    '1': { class_type: 'Text', inputs: { text: 'original' } },
    '2': { class_type: 'Save', inputs: { text: ['1', 0] } },
  };
  await dialog.getByLabel('导入云端工作流', { exact: true }).setInputFiles({ name: 'QA-full.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(fullGraph)) });
  await expect(dialog.getByLabel('工作流提交方式', { exact: true })).toHaveValue('full');
  expect(JSON.parse(await dialog.getByLabel('完整工作流 JSON', { exact: true }).inputValue())).toEqual(fullGraph);
  await dialog.getByLabel('工作流提交方式', { exact: true }).selectOption('id');
  await dialog.getByRole('button', { name: '添加工作流', exact: true }).click();
  await expect(dialog.getByLabel('工作流提交方式', { exact: true })).toHaveValue('full');
  await expect(dialog.getByLabel('完整工作流 JSON', { exact: true })).toHaveValue('{}');
  await dialog.getByRole('button', { name: '移除此工作流配置', exact: true }).click();
  await dialog.getByRole('button', { name: 'QA-full · 副本 已启用', exact: true }).click();
  await dialog.getByLabel('工作流提交方式', { exact: true }).selectOption('full');
  expect(JSON.parse(await dialog.getByLabel('完整工作流 JSON', { exact: true }).inputValue())).toEqual(fullGraph);
  await dialog.getByLabel('输出节点 1', { exact: true }).fill('missing');
  await dialog.getByRole('button', { name: '检查当前工作流', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('输出节点不在完整工作流中');
  await dialog.getByLabel('输出节点 1', { exact: true }).fill('2');
  await dialog.getByRole('button', { name: '添加输入映射', exact: true }).click();
  await dialog.getByLabel('映射 1 节点', { exact: true }).fill('1');
  await dialog.getByLabel('映射 1 字段', { exact: true }).fill('text');
  await dialog.getByRole('button', { name: '检查当前工作流', exact: true }).click();
  await expect(dialog.getByText('当前工作流配置检查通过；尚未保存，未调用云端生成', { exact: true })).toBeVisible();
  const prematureSave = await page.evaluate(async () => (await (await fetch('/api/v1/settings')).json()).cloudWorkflows.some(w => w.name === 'QA-full · 副本'));
  expect(prematureSave).toBe(false);
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByText('设置已保存', { exact: true })).toBeVisible();
  const fullSaved = await page.evaluate(async () => (await (await fetch('/api/v1/settings')).json()).cloudWorkflows.find(w => w.name === 'QA-full · 副本'));
  expect(fullSaved.workflow).toEqual(fullGraph);
  expect(fullSaved.mappings[0]).toMatchObject({ source: 'prompt', nodeId: '1', fieldName: 'text' });
  await dialog.getByRole('button', { name: '移除此工作流配置', exact: true }).click();
  await dialog.getByRole('button', { name: '添加工作流', exact: true }).click();
  await dialog.getByLabel('工作流名称', { exact: true }).fill('QA 图片工作流');
  await dialog.getByLabel('工作流提交方式', { exact: true }).selectOption('id');
  await dialog.getByLabel('RunningHub 工作流 ID', { exact: true }).fill('123');
  await dialog.getByLabel('映射 1 节点', { exact: true }).fill('2');
  await dialog.getByLabel('输出节点 1', { exact: true }).fill('9');
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByRole('status')).toContainText('设置已保存');
  const importedWorkflow = { id: 'qa-video', name: 'QA 视频工作流', kinds: ['video.image_to_video'], enabled: true, version: 1,
    workflowId: '456', nodeInfoList: [], resultNodes: ['8'], mappings: [
      { source: 'prompt', nodeId: '2', fieldName: 'text' }, { source: 'image', nodeId: '3', fieldName: 'image', index: 0 },
    ] };
  await dialog.getByLabel('导入云端工作流', { exact: true }).setInputFiles({ name: 'qa-workflow.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(importedWorkflow)) });
  await expect(dialog.getByLabel('工作流名称', { exact: true })).toHaveValue('QA 视频工作流 · 副本');
  await dialog.getByLabel('工作流名称', { exact: true }).fill('QA 视频工作流');
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByText('设置已保存', { exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(root, '.runtime/qa/cloud-workflows.png'), fullPage: true });
  await dialog.getByRole('button', { name: '费用与并发', exact: true }).click();
  await dialog.getByLabel('选择报价对象', { exact: true }).selectOption({ label: '工作流 / QA 图片工作流' });
  const workflowPrice = await dialog.getByLabel('新价格模型', { exact: true }).inputValue();
  expect(workflowPrice).toMatch(/^workflow\//);
  await dialog.getByRole('button', { name: '添加价格', exact: true }).click();
  await dialog.getByLabel(`${workflowPrice}单价`, { exact: true }).fill('0.2');
  await dialog.getByLabel('选择报价对象', { exact: true }).selectOption({ label: 'QA 文本 B / large' });
  const modelPrice = await dialog.getByLabel('新价格模型', { exact: true }).inputValue();
  expect(modelPrice).toMatch(/^text\/.+\/large$/);
  await dialog.getByRole('button', { name: '添加价格', exact: true }).click();
  await dialog.getByLabel(`${modelPrice}单价`, { exact: true }).fill('0.4');
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByText('设置已保存', { exact: true })).toBeVisible();
  const prices = await page.evaluate(async () => (await (await fetch('/api/v1/settings')).json()).pricing);
  expect(prices[workflowPrice].amount).toBe('0.2');
  expect(prices[modelPrice].amount).toBe('0.4');
  await page.screenshot({ path: path.join(root, '.runtime/qa/profile-pricing.png'), fullPage: true });
  await dialog.getByRole('button', { name: '生成服务', exact: true }).click();
  await dialog.getByRole('button', { name: 'QA 文本 B 已启用', exact: true }).click();
  await dialog.getByRole('button', { name: '移除此服务配置', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'QA 文本 B 已启用', exact: true })).toHaveCount(0);
  await dialog.getByRole('button', { name: '恢复已保存设置', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'QA 文本 B 已启用', exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: '云端工作流', exact: true }).click();
  await dialog.getByRole('button', { name: 'QA 视频工作流 已启用', exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => dialog.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await expect.poll(() => dialog.locator('.settings-body').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await page.screenshot({ path: path.join(root, '.runtime/qa/cloud-workflows-mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 1500, height: 960 });
  await dialog.getByRole('button', { name: '关闭设置', exact: true }).click();
  await page.getByRole('button', { name: '新建项目', exact: true }).click();
  await page.getByLabel('项目名称', { exact: true }).fill('多配置选择 · ' + Date.now());
  await page.getByRole('button', { name: '创建项目', exact: true }).click();
  await page.getByRole('button', { name: '节点', exact: true }).click();
  await page.getByRole('button', { name: '生成分镜图', exact: true }).click();
  await page.getByLabel('生成工作流', { exact: true }).selectOption({ label: 'QA 图片工作流' });
  await page.getByRole('button', { name: '生成视频', exact: true }).click();
  await page.getByLabel('生成工作流', { exact: true }).selectOption({ label: 'QA 视频工作流' });
  await page.locator('.toolbox-node').filter({ hasText: '剧本扩写' }).click();
  await page.getByLabel('文本服务商', { exact: true }).selectOption({ label: 'QA 文本 A（未配置完整）' });
  await page.getByLabel('文本模型', { exact: true }).selectOption('large');
  await page.getByLabel('文本服务商', { exact: true }).selectOption({ label: 'QA 文本 B（未配置完整）' });
  await expect(page.getByLabel('文本模型', { exact: true })).toHaveValue('small');
  await page.getByLabel('文本模型', { exact: true }).selectOption('large');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');
  const selectedProfiles = await savedState();
  expect(selectedProfiles.canvas.nodes.filter(n => n.data.config.workflowId)).toHaveLength(2);
  expect(selectedProfiles.canvas.nodes.find(n => n.data.kind === 'script.expand').data.config.textModel).toBe('large');
  await page.reload();
  await expect(page.locator('.studio-node')).toHaveCount(3);
  expect((await savedState()).canvas.nodes).toEqual(selectedProfiles.canvas.nodes);
  await fitCanvas();
  await node('剧本扩写').locator('header strong').click();
  await expect(page.getByLabel('文本模型', { exact: true })).toHaveValue('large');
  await page.screenshot({ path: path.join(root, '.runtime/qa/node-profile-selection.png'), fullPage: true });
  await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
  await dialog.getByRole('button', { name: '云端工作流', exact: true }).click();
  await dialog.getByRole('button', { name: 'QA 图片工作流 已启用', exact: true }).click();
  await dialog.getByLabel('启用此工作流', { exact: true }).uncheck();
  await dialog.getByRole('button', { name: '保存设置', exact: true }).click();
  await expect(dialog.getByText('设置已保存', { exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: '关闭设置', exact: true }).click();
  await node('生成分镜图').locator('header strong').click();
  await expect(page.getByText('所选工作流已停用或不适用于当前节点。', { exact: true })).toBeVisible();
  if (errors.length) throw new Error(errors.join('\n'));
  console.log('PASS: 画布、分组、预算、ZIP/模板、时间线与合成预览；多文本服务/模型、工作流表单/导入、节点选择/重开、停用提示及窄窗口；无页面异常，未调用云端生成。');
} finally {
  if (savedGenerationProfiles) await page.evaluate(async profiles => {
    const response = await fetch('/api/v1/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profiles) });
    if (!response.ok) throw new Error('恢复生成配置失败');
  }, savedGenerationProfiles).catch(error => console.error(error.message));
  await browser.close();
}
