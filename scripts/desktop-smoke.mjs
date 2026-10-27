// 只安装到本次测试专用目录，关闭仅属于该目录的进程；不触碰已有桌面窗口。
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { mkdir, readFile, readdir, writeFile, access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import net from 'node:net';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps/desktop/package.json'));
const { chromium, expect } = require('@playwright/test');
if (process.platform !== 'win32') throw new Error('桌面安装验收仅支持 Windows');
const bundle = path.join(root, '.runtime/desktop-full-build/release/bundle/nsis');
const installer = process.argv[2] ? path.resolve(process.argv[2]) : path.join(bundle, (await readdir(bundle)).find(name => name.endsWith('-setup.exe')));
const taskRoot = path.join(root, '.runtime/desktop-qa-' + Date.now()), installed = path.join(taskRoot, 'installed'), data = path.join(taskRoot, 'data');
await mkdir(taskRoot, { recursive: true });
const server = net.createServer(); await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const debugPort = server.address().port; await new Promise(resolve => server.close(resolve));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let app, browser, backendPort, windowHandle;
const report = { installer, taskRoot, startedAt: new Date().toISOString(), installation: false, webview: false, savedAndReopened: false, processTreeClosed: false, uninstallation: false };
function powershell(command) { return execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', command], { encoding: 'utf8', windowsHide: true }); }
async function run(file, args, options = {}) {
  await new Promise((resolve, reject) => {
    const child = spawn(file, args, { windowsHide: true, stdio: 'ignore', ...options });
    child.on('error', reject); child.on('exit', code => code === 0 ? resolve() : reject(new Error('进程退出码 ' + code)));
  });
}
async function launch() {
  app = spawn(path.join(installed, 'infinite-canvas.exe'), [], { windowsHide: true, cwd: installed, stdio: 'ignore', env: { ...process.env, FFMPEG_DIR: '',
    CANVAS_DESKTOP_DATA_DIR: data, CANVAS_CONFIG_DIR: path.join(taskRoot, 'config'), CANVAS_QA_DEBUG_PORT: String(debugPort),
    WEBVIEW2_USER_DATA_FOLDER: path.join(taskRoot, 'webview'), WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: '--remote-debugging-port=' + debugPort,
  } });
  app.on('error', error => { report.launchError = error.message; });
  const deadline = Date.now() + 45000;
  let websocket;
  while (Date.now() < deadline) {
    if (app.exitCode !== null) throw new Error('桌面程序提前退出：' + app.exitCode);
    try { const response = await fetch(`http://127.0.0.1:${debugPort}/json/version`); if (response.ok) { websocket = (await response.json()).webSocketDebuggerUrl; if (websocket) break; } } catch {}
    await delay(200);
  }
  if (!websocket) throw new Error('WebView2 调试端口未在 45 秒内就绪');
  browser = await chromium.connectOverCDP(websocket, { noDefaults: true });
  const context = browser.contexts()[0];
  let page;
  for (let i = 0; i < 100; i++) {
    page = context.pages().find(page => page.url().includes('127.0.0.1:') && !page.url().includes('devtools'));
    if (page) break;
    await delay(100);
  }
  if (!page) throw new Error('未找到工作台 WebView 页面');
  backendPort = new URL(page.url()).port;
  await expect(page.locator('.app-shell')).toBeVisible({ timeout: 15000 });
  report.webview = true;
  // 将测试窗口隐藏；CDP 仍可验证真实 WebView2。
  windowHandle = powershell(`(Get-Process -Id ${app.pid}).MainWindowHandle.ToInt64()`).trim();
  powershell(`Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class QAHide { [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n); }'; [QAHide]::ShowWindow([IntPtr]${windowHandle},0) | Out-Null`);
  return page;
}
async function closeApp() {
  const pid = app.pid;
  powershell(`Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class QAClose { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l); }'; [QAClose]::PostMessage([IntPtr]${windowHandle},0x0010,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null`);
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline && app.exitCode === null) await delay(100);
  if (app.exitCode === null) throw new Error('桌面窗口关闭未终止进程');
  browser = undefined;
  await delay(300);
  const escaped = installed.replaceAll("'", "''");
  const survivors = powershell(`@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith('${escaped}',[StringComparison]::OrdinalIgnoreCase) }).Count`).trim();
  if (survivors !== '0') throw new Error('桌面关闭后仍有安装目录内的子进程');
  try { await fetch(`http://127.0.0.1:${backendPort}/healthz`); throw new Error('桌面关闭后后端仍在监听'); } catch (error) { if (error.message === '桌面关闭后后端仍在监听') throw error; }
  report.processTreeClosed = true;
}
try {
  await run(installer, ['/S', '/D=' + installed]);
  await access(path.join(installed, 'infinite-canvas.exe')); await access(path.join(installed, 'canvas-backend.exe'));
  report.installation = true;
  let page = await launch();
  await expect(page.getByRole('heading', { name: '新建短剧项目' })).toBeVisible();
  await page.getByLabel('项目名称').fill('真实桌面验收');
  await page.getByRole('button', { name: '创建项目', exact: true }).click();
  await page.getByRole('button', { name: '添加故事节点', exact: true }).click();
  await page.getByRole('textbox', { name: '故事内容', exact: true }).fill('桌面安装后保存，关闭后重新打开验证。');
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect(page.locator('.save-status')).toContainText('已保存到本机');
  await page.screenshot({ path: path.join(taskRoot, 'desktop.png') });
  await closeApp();
  page = await launch();
  await expect(page.locator('.studio-node')).toHaveCount(1);
  await page.locator('.studio-node').click();
  await expect(page.getByRole('textbox', { name: '故事内容', exact: true })).toHaveValue('桌面安装后保存，关闭后重新打开验证。');
  report.savedAndReopened = true;
  const sample = path.join(taskRoot, 'media-test.mp4');
  await run(path.join(installed, 'media/ffmpeg.exe'), ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=white:s=64x64:r=25', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '1', '-c:a', 'aac', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', sample]);
  await access(path.join(installed, 'media/LICENSE')); await access(path.join(installed, 'media/README.txt'));
  const mediaJob = await page.evaluate(async bytes => {
    const opts = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const p = await (await fetch('/api/v1/projects', opts('POST', { name: '安装版媒体验收' }))).json();
    const form = new FormData(); form.set('projectId', p.id); form.set('file', new Blob([new Uint8Array(bytes)], { type: 'video/mp4' }), 'sample.mp4');
    const asset = await (await fetch('/api/v1/assets/import', { method: 'POST', body: form })).json();
    const c = await (await fetch(`/api/v1/canvases/${p.id}`)).json();
    c.nodes = [['video', 'asset.video', { assetId: asset.id }], ['extract', 'audio.extract', {}]].map(([id, kind, config], i) => ({ id, type: 'studio', position: { x: i * 350, y: 0 }, data: { kind, config } }));
    c.edges = [{ id: 'v', source: 'video', target: 'extract', sourceHandle: 'video', targetHandle: 'video' }];
    const req = opts('PUT', c); req.headers['If-Match'] = String(c.version);
    if (!(await fetch(`/api/v1/canvases/${p.id}`, req)).ok) throw new Error('安装版画布写入失败');
    const submitted = await fetch('/api/v1/runs', opts('POST', { projectId: p.id, nodeIds: ['extract'] }));
    if (!submitted.ok) throw new Error('安装版提取任务提交失败');
    return (await submitted.json()).id;
  }, [...await readFile(sample)]);
  await expect.poll(() => page.evaluate(async id => (await (await fetch(`/api/v1/runs/${id}`)).json()).tasks.find(t => t.node_id === 'extract')?.status, mediaJob), { timeout: 20000 }).toBe('completed');
  report.bundledMediaExtraction = true;
  // Exercise the installed WebView's native download handler, not Playwright's download override.
  await page.evaluate(() => {
    window.qaDownloads = [];
    window.addEventListener('canvas-download', event => window.qaDownloads.push(event.detail));
  });
  const downloadAsset = await page.evaluate(async id => {
    const run = await (await fetch(`/api/v1/runs/${id}`)).json();
    const aid = run.tasks.find(t => t.node_id === 'extract').output.assets[0];
    return { aid, bytes: [...new Uint8Array(await (await fetch(`/api/v1/assets/${aid}/content`)).arrayBuffer())] };
  }, mediaJob);
  const savedPaths = [];
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.evaluate(aid => {
      const a = document.createElement('a'); a.href = `/api/v1/assets/${aid}/content?download=true`;
      a.download = 'download-test.wav'; a.textContent = 'QA download'; a.id = 'qa-download'; document.body.append(a);
    }, downloadAsset.aid);
    await page.locator('#qa-download').click();
    try {
      await expect.poll(() => page.evaluate(() => window.qaDownloads.filter(e => e.status === 'completed').length), { timeout: 15000 }).toBe(attempt + 1);
    } catch (error) {
      console.log('Download events:', await page.evaluate(() => window.qaDownloads));
      console.log('Download HTTP:', await page.evaluate(async aid => { const r = await fetch(`/api/v1/assets/${aid}/content?download=true`); return { status: r.status, disposition: r.headers.get('content-disposition') }; }, downloadAsset.aid));
      throw error;
    }
    const saved = await page.evaluate(() => window.qaDownloads.filter(e => e.status === 'completed').at(-1).path);
    if (!path.resolve(saved).startsWith(path.resolve(data, 'downloads') + path.sep)) throw new Error('Download escaped QA directory');
    expect(await readFile(saved)).toEqual(Buffer.from(downloadAsset.bytes)); savedPaths.push(saved);
    await page.locator('#qa-download').evaluate(a => a.remove());
  }
  expect(savedPaths[0]).not.toBe(savedPaths[1]);
  report.assetDownload = true;
  report.downloadCollisionSafe = true;
  await closeApp();
  const uninstaller = (await readdir(installed)).find(name => /^uninstall.*\.exe$/i.test(name));
  if (!uninstaller) throw new Error('没有找到卸载程序');
  // _?= 禁止卸载程序复制到临时目录，保证可等待真正卸载结束。
  await run(path.join(installed, uninstaller), ['/S', '_?=' + installed]);
  const leftover = await access(path.join(installed, 'infinite-canvas.exe')).then(() => true, () => false);
  if (leftover) throw new Error('卸载后应用程序仍存在');
  report.uninstallation = true;
  console.log('PASS: 独立安装、真实 WebView2、保存重开、窗口关闭后进程树退出、卸载。');
} finally {
  if (app && app.exitCode === null) execFileSync('taskkill.exe', ['/PID', String(app.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
  if (browser) await browser.close().catch(() => {});
  report.finishedAt = new Date().toISOString();
  await mkdir(path.join(root, '.runtime/qa'), { recursive: true });
  await writeFile(path.join(root, '.runtime/qa/desktop.json'), JSON.stringify(report, null, 2));
}
