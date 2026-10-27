import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { requireQaSession } from './qa-session.mjs';
const require = createRequire(new URL('../apps/desktop/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const { url, dataDir } = await requireQaSession();
const next = path.resolve(dataDir, '..', 'new-projects');
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(url); await expect(page.locator('.app-shell')).toBeVisible();
  if (await page.getByRole('heading', { name: '新建短剧项目' }).isVisible()) {
    await page.getByRole('button', { name: '设置数据保存路径', exact: true }).click();
    await expect(page.getByLabel('当前数据目录')).toHaveValue(dataDir);
    await expect(page.getByRole('button', { name: '保存设置', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: '关闭设置' }).click();
    await expect(page.getByRole('heading', { name: '新建短剧项目' })).toBeVisible();
    await page.getByLabel('项目名称').fill('Storage QA');
    await page.getByRole('button', { name: '创建项目', exact: true }).click();
  }
  const open = async () => {
    await page.getByRole('button', { name: '打开工作台设置' }).click();
    await page.getByRole('button', { name: '数据存储', exact: true }).click();
  };
  await open();
  await expect(page.getByLabel('当前数据目录')).toHaveValue(dataDir);
  if (await page.getByRole('button', { name: '选择文件夹', exact: true }).isVisible()) {
    let selection = next;
    await page.route('**/api/v1/settings/storage/browse', route => route.fulfill({ json: { directory: selection } }));
    await page.getByRole('button', { name: '选择文件夹', exact: true }).click();
    await expect(page.getByLabel('默认保存路径')).toHaveValue(next);
    await expect(page.getByText('已选择文件夹，请点击“保存数据路径”应用更改')).toBeVisible();
    const saved = await page.evaluate(async () => (await fetch('/api/v1/settings/storage')).json());
    expect(saved.nextDirectory).toBe(dataDir);
    selection = null;
    await page.getByRole('button', { name: '选择文件夹', exact: true }).click();
    await expect(page.getByRole('button', { name: '选择文件夹', exact: true })).toBeEnabled();
    await expect(page.getByLabel('默认保存路径')).toHaveValue(next);
    await page.unroute('**/api/v1/settings/storage/browse');
  }
  await page.getByLabel('默认保存路径').fill('relative/path');
  await page.getByRole('button', { name: '保存数据路径', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('绝对路径');
  await page.getByLabel('默认保存路径').fill(next);
  await page.getByRole('button', { name: '保存数据路径', exact: true }).click();
  await expect(page.getByText('待重启：下次使用 ' + next, { exact: true })).toBeVisible();
  await expect(page.getByLabel('当前数据目录')).toHaveValue(dataDir);
  await page.getByRole('button', { name: '关闭设置' }).click();
  await open();
  await expect(page.getByLabel('默认保存路径')).toHaveValue(next);
  await mkdir('.runtime/qa', { recursive: true });
  await page.screenshot({ path: '.runtime/qa/storage-settings.png' });
  await page.getByRole('button', { name: '撤销目录更改', exact: true }).click();
  await expect(page.getByLabel('默认保存路径')).toHaveValue(dataDir);
  await expect(page.getByRole('button', { name: '撤销目录更改', exact: true })).toBeDisabled();
  console.log('PASS: storage entry, directory validation, pending restart, persistence, cancellation');
} finally { await browser.close(); }
