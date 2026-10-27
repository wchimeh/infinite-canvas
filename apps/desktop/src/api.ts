export class ApiError extends Error {
  constructor(message: string, public status: number, public retryable = false) { super(message); }
}

export async function api<T>(path: string, options: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  const { timeoutMs = ['GET', 'HEAD'].includes((options.method || 'GET').toUpperCase()) ? 15000 : 0, signal, ...request } = options;
  const controller = new AbortController();
  const cancel = () => controller.abort(signal?.reason);
  if (signal?.aborted) cancel();
  else signal?.addEventListener('abort', cancel, { once: true });
  let timedOut = false;
  const timer = timeoutMs > 0 ? setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs) : undefined;
  try {
    const response = await fetch('/api/v1' + path, {
      credentials: 'same-origin', ...request, signal: controller.signal,
      headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      if (controller.signal.aborted) throw controller.signal.reason;
      throw new ApiError(body.message || `请求失败（${response.status}）`, response.status, [408, 429, 502, 503, 504].includes(response.status));
    }
    return await response.json();
  } catch (error) {
    if (timedOut && !signal?.aborted) throw new ApiError(`查询超时（${Math.round(timeoutMs / 1000)} 秒），请检查本地服务是否正常`, 0, true);
    if (!controller.signal.aborted && error instanceof TypeError) throw new ApiError('无法连接本地服务，请检查服务是否运行', 0, true);
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}

export async function connectSession() {
  const params = new URLSearchParams(location.hash.slice(1));
  const token = params.get('token');
  if (token) {
    history.replaceState(null, '', location.pathname + location.search);
    await api('/session', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
  }
  // 无 token 时仅尝试既有 HttpOnly 会话，失败显示启动器指引。
}

export const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });
export const mediaUrl = (id: string) => '/api/v1/assets/' + encodeURIComponent(id) + '/content';
export const downloadUrl = (id: string) => mediaUrl(id) + '?download=true';
export const thumbnailUrl = (id: string) => '/api/v1/assets/' + encodeURIComponent(id) + '/thumbnail';
