import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { transformWithEsbuild } from 'vite';

const source = await readFile(new URL('./timelineLayout.ts', import.meta.url), 'utf8');
const { code } = await transformWithEsbuild(source, 'timelineLayout.ts', { loader: 'ts', format: 'esm' });
const { resizeTimeline } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);

test('已保存的全屏片段随画幅一起改变尺寸，未保存片段保持自动适配', () => {
  const timeline = { width: 1080, height: 1920, fps: 30, version: 1, audio: [], subtitles: [], clips: [
    { id: 'saved', transform: { x: 0, y: 0, width: 1080, height: 1920, fit: 'contain', opacity: 1 } },
    { id: 'new' }, { id: 'fit', transform: { fit: 'cover' } },
  ] };
  const original = structuredClone(timeline);
  const result = resizeTimeline(timeline, 1920, 1080);
  assert.deepEqual(result.clips[0].transform, { x: 0, y: 0, width: 1920, height: 1080, fit: 'contain', opacity: 1 });
  assert.equal(result.clips[1].transform, undefined);
  assert.deepEqual(result.clips[2].transform, { fit: 'cover' });
  assert.deepEqual(timeline, original);
});

test('叠加层保持相对布局，尺寸为合法偶数且位置不超出边界', () => {
  const timeline = { width: 1920, height: 1080, fps: 24, audio: [], subtitles: [], clips: [
    { track: 'V2', transform: { x: 960, y: 270, width: 480, height: 270, fit: 'cover', opacity: 0.5 } },
    { track: 'V2', transform: { x: -3840, y: 3840, width: 3840, height: 2 } },
  ] };
  const result = resizeTimeline(timeline, 1080, 1920);
  assert.deepEqual(result.clips[0].transform, { x: 540, y: 480, width: 270, height: 480, fit: 'cover', opacity: 0.5 });
  assert.equal(result.clips[1].transform.y, 3840);
  for (const clip of result.clips) {
    for (const key of ['width', 'height']) {
      assert.equal(clip.transform[key] % 2, 0);
      assert.ok(clip.transform[key] >= 2 && clip.transform[key] <= 3840);
    }
  }
});
