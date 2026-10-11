import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  const project = { id: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', name: 'Shot nodes QA', settings: { cloudEnabled: false }, version: 1 };
  const shots = [
    { title: '相遇', visualPrompt: '两个人在公园相遇', dialogue: '你好。', durationMs: 8000, cameraMove: '固定镜头' },
    { title: '告别', visualPrompt: '两个人挥手告别', dialogue: '再见。', durationMs: 12000, cameraMove: '缓慢拉远' },
  ];
  const node = (id, kind, x, selected = false) => ({ id, type: 'studio', position: { x, y: 100 }, selected,
    data: { kind, title: kind, config: {}, status: 'idle' } });
  let canvas = { nodes: [node('source', 'shots.extract', -250), node('select', 'shots.select', 80, true),
    node('expand', 'prompt.video_expand', 410), node('video', 'video.image_to_video', 740)],
    edges: [['source', 'select'], ['select', 'expand'], ['expand', 'video']].map(([source, target]) => ({ id: `${source}-${target}`, source, target, sourceHandle: 'text', targetHandle: 'text', data: { kind: 'data' } })),
    viewport: { x: 0, y: 0, zoom: 0.8 }, version: 1 };
  let tasks = [{ id: 'source-task', node_id: 'source', created_at: Date.now() / 1000 + 100, status: 'completed', snapshot: { config: {}, kind: 'shots.extract' }, output: { shots, text: JSON.stringify(shots) } }];
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/session')) return route.continue();
    if (route.request().method() !== 'GET') {
      const body = route.request().postDataJSON() || {};
      if (path.includes('/canvases/')) canvas = { ...body, version: canvas.version + 1 };
      return route.fulfill({ json: path.includes('/canvases/') ? canvas : body });
    }
    if (path.endsWith('/projects')) return route.fulfill({ json: [project] });
    if (path.endsWith(`/projects/${project.id}`)) return route.fulfill({ json: project });
    if (path.includes('/canvases/')) return route.fulfill({ json: canvas });
    if (path.endsWith('/tasks')) return route.fulfill({ json: tasks });
    if (path.endsWith('/assets')) return route.fulfill({ json: [] });
    if (path.endsWith('/people')) return route.fulfill({ json: { shots: [], characters: [], locations: [], version: 1 } });
    if (path.endsWith('/timeline')) return route.fulfill({ json: { clips: [], audio: [], subtitles: [], fps: 24, width: 1080, height: 1920, version: 1 } });
    if (path.endsWith('/definitions')) {
      const response = await route.fetch(), definitions = await response.json();
      definitions['shots.select'] = { displayName: '分镜选择', inputs: { text: 'text' }, outputs: { text: 'text' } };
      definitions['prompt.video_expand'] = { displayName: '视频提示词扩写', inputs: { text: 'text', image: 'image' }, outputs: { text: 'text' } };
      return route.fulfill({ json: definitions });
    }
    if (path.endsWith('/generation-options')) return route.fulfill({ json: {
      textServices: [{ id: 'legacy', name: 'QA text service', enabled: true, ready: true, models: ['vision-qa'], defaultModel: 'vision-qa' }],
      workflows: [{ id: 'builtin-minimax-h3', name: 'MiniMax H3', enabled: true, builtin: 'minimax_h3', kinds: ['video.image_to_video'] }],
    } });
    return route.continue();
  });
  await page.goto(url);
  await expect(page.getByRole('button', { name: /分镜选择$/ })).toBeVisible();
  await expect(page.getByRole('button', { name: '视频提示词扩写', exact: true })).toBeVisible();
  const selection = page.locator('[data-id="select"]').getByLabel('选择分镜');
  await expect(selection).toBeEnabled();
  await selection.selectOption('1');
  await expect(page.locator('.inspector').getByLabel('选择分镜')).toHaveValue('1');
  await expect(page.locator('[data-id="select"]').getByText('两个人挥手告别')).toBeVisible();
  await expect(page.getByRole('button', { name: '输出所选分镜', exact: true })).toBeEnabled();
  await expect(page.getByLabel('生成工作流')).toHaveCount(0);
  await page.getByRole('button', { name: '保存', exact: true }).click();
  await expect.poll(() => canvas.nodes.find(n => n.id === 'select').data.config.shotIndex).toBe(1);
  expect(canvas.nodes.find(n => n.id === 'expand').data.config.seconds).toBe(12);
  expect(canvas.nodes.find(n => n.id === 'video').data.config.seconds).toBe(12);
  await page.reload();
  await expect(selection).toHaveValue('1');
  // Changed upstream content must invalidate the saved selection.
  tasks = [{ ...tasks[0], output: { ...tasks[0].output, shots: [shots[0], { ...shots[1], title: '新的告别' }] } }];
  await page.reload();
  await expect(selection).toHaveValue('');
  await page.locator('[data-id="select"] header').click();
  await expect(page.locator('.inspector').getByText('原分镜已变化或时长不合规，请重新选择。')).toBeVisible();
  await expect(page.getByRole('button', { name: '输出所选分镜', exact: true })).toBeDisabled();
  await selection.selectOption('1');
  await page.locator('[data-id="expand"] header').click();
  await expect(page.getByLabel('文本服务商')).toBeVisible();
  await expect(page.getByLabel('文本模型')).toHaveValue('vision-qa');
  await expect(page.getByLabel('扩写目标时长（秒）')).toHaveValue('12');
  await expect(page.getByLabel('生成工作流')).toHaveCount(0);
  await expect(page.getByLabel('生成服务', { exact: true })).toHaveCount(0);
  await expect(page.getByText(/参考规范输出六段英文/)).toBeVisible();
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/shot-nodes.png', fullPage: true });
  expect(errors).toEqual([]);
  console.log('PASS: shot selection, invalidation, persistence, inherited durations and video prompt expansion settings; all writes mocked');
} finally { await browser.close(); }
