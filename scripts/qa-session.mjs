import { readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export async function requireQaSession(env = process.env) {
  const fail = () => { throw new Error('写入验收需要隔离 QA 会话：CANVAS_QA=1，显式 CANVAS_SESSION_FILE，以及同一 .runtime/qa-* 目录内的 dataDir/configDir 清单。禁止使用日常会话。'); };
  if (env.CANVAS_QA !== '1' || !env.CANVAS_SESSION_FILE) fail();
  try {
    const sessionFile = await realpath(env.CANVAS_SESSION_FILE);
    const taskRoot = path.dirname(sessionFile);
    const runtime = await realpath(path.join(root, '.runtime'));
    if (path.dirname(taskRoot) !== runtime || !/^qa-.+/.test(path.basename(taskRoot))) fail();
    const session = JSON.parse(await readFile(sessionFile, 'utf8'));
    if (session.qa !== true || !session.dataDir || !session.configDir) fail();
    for (const directory of [session.dataDir, session.configDir]) {
      const relative = path.relative(taskRoot, await realpath(directory));
      if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) fail();
    }
    const url = new URL(session.url);
    if (url.protocol !== 'http:' || !['localhost', '127.0.0.1'].includes(url.hostname) || !url.port || url.port === '5173' || url.username || url.password) fail();
    return session;
  } catch { fail(); }
}
