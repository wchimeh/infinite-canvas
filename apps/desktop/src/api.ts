export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch('/api/v1' + path, {
    credentials: 'same-origin', ...options,
    headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message || `请求失败（${response.status}）`);
  }
  return response.json();
}

export async function connectSession() {
  const params = new URLSearchParams(location.hash.slice(1));
  const token = params.get('token');
  if (token) {
    await api('/session', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
    history.replaceState(null, '', location.pathname + location.search);
  }
  // 无 token 时仅尝试既有 HttpOnly 会话，失败显示启动器指引。
}

export const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });
export const mediaUrl = (id: string) => '/api/v1/assets/' + encodeURIComponent(id) + '/content';
export const thumbnailUrl = (id: string) => '/api/v1/assets/' + encodeURIComponent(id) + '/thumbnail';
