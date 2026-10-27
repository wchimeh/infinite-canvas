import { useEffect, useState } from 'react';
import { api, json } from './api';

type StorageStatus = { currentDirectory: string; nextDirectory: string; restartRequired: boolean; startupError: string; directoryPickerAvailable?: boolean };

export function StorageSettings() {
  const [status, setStatus] = useState<StorageStatus>();
  const [directory, setDirectory] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  useEffect(() => {
    let active = true;
    void api<StorageStatus>('/settings/storage').then(value => {
      if (active) { setStatus(value); setDirectory(value.nextDirectory); }
    }).catch(e => { if (active) setError(String(e.message || e)); });
    return () => { active = false; };
  }, []);
  async function browse() {
    setBusy(true); setError(''); setMessage('');
    try {
      const result = await api<{ directory: string | null }>('/settings/storage/browse', json('POST', { directory }));
      if (result.directory) { setDirectory(result.directory); setMessage('已选择文件夹，请点击“保存数据路径”应用更改'); }
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  async function save(cancel = false) {
    setBusy(true); setError(''); setMessage('');
    try {
      const value = await api<StorageStatus>('/settings/storage', cancel ? { method: 'DELETE' } : json('PUT', { directory }));
      setStatus(previous => ({ ...value, directoryPickerAvailable: previous?.directoryPickerAvailable })); setDirectory(value.nextDirectory);
      setMessage(cancel ? '已撤销目录更改，继续使用当前目录' : value.restartRequired ? '路径已保存。请保存画布并完全退出、重新启动应用后生效。' : '已保存，当前正在使用此目录');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  return <section><h3>项目数据保存位置</h3>
    <p className="muted">包含全部项目的画布、素材、生成记录和缓存。服务配置和密钥继续保存在原来的系统位置。</p>
    {status && <><label>当前数据目录<input aria-label="当前数据目录" readOnly value={status.currentDirectory}/></label>
      <label>默认保存路径<input aria-label="默认保存路径" disabled={busy} value={directory} placeholder="例如 D:\InfiniteCanvasData" onChange={e => setDirectory(e.target.value)}/></label>
      {status.directoryPickerAvailable && <button type="button" disabled={busy} onClick={() => void browse()}>选择文件夹</button>}
      <small>请输入专用文件夹的完整路径；保存后重启生效。已有数据仍保留在原目录，不会自动搬迁或删除。切换到空目录后不会显示原目录中的项目。</small>
      {status.restartRequired && <p role="status">待重启：下次使用 {status.nextDirectory}</p>}
      {status.startupError && <p role="alert" className="error-box">新目录未能启用，当前已回退：{status.startupError}</p>}
      <div className="field-row"><button disabled={busy || !directory.trim()} onClick={() => void save()}>保存数据路径</button>
        <button disabled={busy || !status.restartRequired} onClick={() => void save(true)}>撤销目录更改</button></div>
    </>}
    {error && <p role="alert" className="error-box">{error}</p>}{message && <p role="status">{message}</p>}
    {!status && !error && <p>正在读取数据位置…</p>}
  </section>;
}
