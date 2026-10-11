import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url } = JSON.parse(await readFile(process.env.CANVAS_SESSION_FILE || new URL('../.runtime/session.json', import.meta.url), 'utf8'));
await mkdir(new URL('../.runtime/qa/', import.meta.url), { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  await expect(page.locator('.app-shell')).toBeVisible();
  for (const width of [1440, 1024, 390]) {
    await page.setViewportSize({ width, height: 960 });
    await page.getByRole('button', { name: /^任务中心/ }).click();
    await expect(page.locator('.queue-summary-items > div')).toHaveCount(3);
    await expect(page.locator('.timeline-meta')).toBeHidden();
    const fits = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
    expect(fits, `workbench overflow at ${width}`).toBe(true);
    const canvasHeight = await page.locator('.react-flow').evaluate(el => el.getBoundingClientRect().height);
    expect(canvasHeight, `canvas height at ${width}`).toBeGreaterThan(200);
    await expect(page.locator('.provider-status .check-row')).toBeVisible();
    await page.screenshot({ path: `.runtime/qa/style-after-${width}.png`, fullPage: true });
    await page.getByRole('button', { name: '打开工作台设置', exact: true }).click();
    await page.getByRole('button', { name: '费用与并发', exact: true }).click();
    await expect(page.getByLabel('图片＋视频并发数', { exact: true })).toBeVisible();
    const dialogFits = await page.locator('.settings-dialog').evaluate(el => el.scrollWidth <= el.clientWidth + 1);
    expect(dialogFits, `settings overflow at ${width}`).toBe(true);
    await page.screenshot({ path: `.runtime/qa/style-settings-${width}.png`, fullPage: true });
    await page.getByRole('button', { name: '关闭设置', exact: true }).click();
  }
  expect(errors).toEqual([]);
  console.log('PASS: desktop/tablet/mobile, queue layout, settings, timeline tool visibility, no page errors');
} finally { await browser.close(); }
