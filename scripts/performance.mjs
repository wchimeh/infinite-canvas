// 使用独立无个人资料的浏览器，创建独立性能项目，不执行任何生成。
import { createRequire } from 'node:module';
import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { requireQaSession } from './qa-session.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps/desktop/package.json'));
const { chromium, expect } = require('@playwright/test');
const { url } = await requireQaSession();
const browser = await chromium.launch({ headless: true, ...(process.env.TEST_BROWSER_PATH ? { executablePath: process.env.TEST_BROWSER_PATH } : {}) });
const page = await browser.newPage({ viewport: { width: 1500, height: 960 } });
const cpuRate = Number(process.env.CANVAS_CPU_RATE || 1);
if (![1, 4, 6].includes(cpuRate)) throw new Error('CANVAS_CPU_RATE must be 1, 4 or 6');
const cdp = await page.context().newCDPSession(page);
await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpuRate });
await cdp.send('Performance.enable');
const reportName = process.env.CANVAS_PERF_REPORT || 'performance';
if (!/^[a-z0-9-]+$/.test(reportName)) throw new Error('Invalid report name');
const errors = [];
page.on('pageerror', error => errors.push(error.message));
await page.addInitScript(() => {
  window.qaLongTasks = [];
  new PerformanceObserver(list => window.qaLongTasks.push(...list.getEntries().map(entry => ({ start: entry.startTime, duration: entry.duration })))).observe({ type: 'longtask', buffered: true });
});
try {
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  const pid = await page.evaluate(async () => {
    const request = async (path, method, body, headers = {}) => {
      const response = await fetch('/api/v1' + path, { method, body: body ? JSON.stringify(body) : undefined, headers: { 'Content-Type': 'application/json', ...headers } });
      if (!response.ok) throw new Error('性能项目准备失败：' + response.status);
      return response.json();
    };
    const project = await request('/projects', 'POST', { name: '性能验收 200 节点 / 300 连线 ' + Date.now() });
    const canvas = await request('/canvases/' + project.id, 'GET');
    canvas.nodes = Array.from({ length: 200 }, (_, i) => ({ id: 'node-' + i, type: 'studio', position: { x: (i % 20) * 330, y: Math.floor(i / 20) * 280 }, data: { kind: 'image.generate', title: '镜头 ' + i, status: 'idle', config: { prompt: '性能验收，无云调用' } } }));
    canvas.edges = Array.from({ length: 199 }, (_, i) => ({ id: 'edge-' + i, source: 'node-' + i, target: 'node-' + (i + 1), sourceHandle: 'image', targetHandle: 'image', data: { kind: 'data' } }));
    canvas.edges.push(...Array.from({ length: 101 }, (_, i) => ({ id: 'cross-' + i, source: 'node-' + i, target: 'node-' + (i + 2), sourceHandle: 'image', targetHandle: 'image', data: { kind: 'data' } })));
    await request('/canvases/' + project.id, 'PUT', canvas, { 'If-Match': String(canvas.version) });
    localStorage.setItem('canvas-last-project', project.id);
    return project.id;
  });
  const started = Date.now();
  await page.reload();
  await expect(page.locator('.canvas-toolbar .muted')).toContainText('200 节点 · 300 连线', { timeout: 30000 });
  const warmStartMs = Date.now() - started;
  await page.locator('.react-flow__controls-fitview').click();
  await page.waitForTimeout(400);
  await page.evaluate(() => { window.qaLongTasks = []; });
  const metricsBefore = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
  const frameSample = page.evaluate(() => new Promise(resolve => {
    const frames = []; let last = performance.now(), start = last;
    function frame(now) { frames.push(now - last); last = now; if (now - start < 2500) requestAnimationFrame(frame); else resolve({ frames, longTasks: window.qaLongTasks }); }
    requestAnimationFrame(frame);
  }));
  const pane = await page.locator('.react-flow__pane').boundingBox();
  await page.mouse.move(pane.x + pane.width / 2, pane.y + pane.height / 2);
  await page.mouse.wheel(0, -150);
  await page.keyboard.down('Space'); await page.mouse.down();
  await page.mouse.move(pane.x + pane.width / 2 + 80, pane.y + pane.height / 2 + 30, { steps: 20 });
  await page.mouse.up(); await page.keyboard.up('Space');
  const sample = await frameSample;
  const metricsAfter = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
  const workMs = Object.fromEntries(['ScriptDuration', 'LayoutDuration', 'RecalcStyleDuration', 'TaskDuration'].map(name => [name, Math.round((metricsAfter[name] - metricsBefore[name]) * 1000)]));
  const frames = sample.frames.slice(1).sort((a, b) => a - b);
  const fps = 1000 / (frames.reduce((a, b) => a + b, 0) / frames.length);
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');
  const snapshot = await page.evaluate(async pid => (await fetch('/api/v1/canvases/' + pid)).json(), pid);
  expect(snapshot.nodes).toHaveLength(200); expect(snapshot.edges).toHaveLength(300);
  expect(errors).toEqual([]);
  const report = { measuredAt: new Date().toISOString(), machine: process.platform + '/' + process.arch, browser: browser.version(), projectId: pid,
    cpuRate, workMs, nodes: 200, edges: 300, warmStartMs, averageFps: Number(fps.toFixed(2)), frameP95Ms: Number(frames[Math.floor(frames.length * 0.95)].toFixed(2)),
    longTaskCount: sample.longTasks.length, longestTaskMs: Math.max(0, ...sample.longTasks.map(task => task.duration)), errors, functional: 'passed',
    targets: { warmStartUnder5s: warmStartMs < 5000, interactiveFpsAtLeast30: fps >= 30 }, note: '本机无头 Chromium 实测；不等同于所有目标机器性能。' };
  await mkdir(path.join(root, '.runtime/qa'), { recursive: true });
  await writeFile(path.join(root, `.runtime/qa/${reportName}.json`), JSON.stringify(report, null, 2));
  await page.screenshot({ path: path.join(root, `.runtime/qa/${reportName}.png`) });
  console.log(JSON.stringify(report, null, 2));
} finally { await browser.close(); }
