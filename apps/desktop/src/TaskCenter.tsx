import { useEffect, useRef, useState } from 'react';
import { useStudio } from './store';
import { MediaResult } from './MediaResult';
import { STATUS, type Task } from './types';
import { taskInformation } from './taskInformation';
import { QueueSummary } from './QueueSummary';

function queueOf(task: Task) {
  const kind = task.snapshot.kind;
  if (['story.prompt', 'text.concat', 'shots.select', 'frame.extract', 'audio.extract', 'audio.trim', 'video.trim'].includes(kind) || kind.startsWith('asset.') || kind.endsWith('.reference') || ('adopted' in task.snapshot && task.snapshot.adopted)) return 'local';
  if (kind.startsWith('image.') || kind.startsWith('video.')) return 'media';
  return kind.startsWith('audio.') ? 'audio' : 'text';
}

export function TaskCenter({ cancel, retry }: { cancel: (id: string) => void; retry: (id: string, uncertain: boolean) => void }) {
  const tasks = useStudio(s => s.tasks), nodes = useStudio(s => s.nodes), assets = useStudio(s => s.assets);
  const [queue, setQueue] = useState('all'), [status, setStatus] = useState('all'), [previewId, setPreviewId] = useState('');
  const [search, setSearch] = useState('');
  const query = search.trim().toLocaleLowerCase();
  const nodeNames = new Map(nodes.map(node => [node.id, node.data.title]));
  const hasFilters = queue !== 'all' || status !== 'all' || search !== '';
  function clearFilters() { setQueue('all'); setStatus('all'); setSearch(''); }
  const dialog = useRef<HTMLDialogElement>(null);
  const copyRequest = useRef(0);
  const [copyState, setCopyState] = useState('');
  useEffect(() => { copyRequest.current += 1; setCopyState(''); return () => { copyRequest.current += 1; }; }, [previewId]);
  async function copyText(text: string) {
    const request = ++copyRequest.current;
    setCopyState('正在复制…');
    try {
      await navigator.clipboard.writeText(text);
      if (request === copyRequest.current) setCopyState('已复制全文');
    } catch {
      if (request === copyRequest.current) setCopyState('无法访问剪贴板，请选中下方正文手动复制。');
    }
  }
  const preview = tasks.find(task => task.id === previewId);
  useEffect(() => { if (preview) dialog.current?.showModal(); else dialog.current?.close(); }, [previewId, !!preview]);
  const filtered = tasks.filter(task => (!query || [nodeNames.get(task.node_id), task.node_id, task.id, taskInformation(task)].join(' ').toLocaleLowerCase().includes(query)) && (queue === 'all' || queueOf(task) === queue) && (status === 'all' ||
    (status === 'active' ? ['queued', 'running', 'cancel_requested'].includes(task.status) :
      status === 'failed' ? ['failed', 'blocked'].includes(task.status) : task.status === status)));
  return <div className="task-table"><QueueSummary/>
    <div className="task-filters"><label className="task-search">搜索<input type="search" aria-label="搜索当前项目任务" placeholder="节点名称、任务 ID 或任务信息" value={search} onChange={e => setSearch(e.target.value)}/></label><label>队列<select aria-label="筛选任务队列" value={queue} onChange={e => setQueue(e.target.value)}><option value="all">全部队列</option><option value="text">LLM 文本</option><option value="media">图片＋视频</option><option value="audio">音频</option><option value="local">本地输入 / 已采用素材</option></select></label>
      <label>状态<select aria-label="筛选任务状态" value={status} onChange={e => setStatus(e.target.value)}><option value="all">全部状态</option><option value="active">待处理</option><option value="completed">已完成</option><option value="failed">失败 / 上游未完成</option><option value="cancelled">已取消</option></select></label><small>当前项目 {filtered.length} / {tasks.length} 条</small></div>
    {hasFilters && <div className="task-filter-reset"><button onClick={clearFilters}>清除筛选</button><small role="status">找到 {filtered.length} 条任务</small></div>}
    <div className="task-table-head"><span>节点 / 运行</span><span>状态</span><span>任务信息</span><span>操作</span></div>
    {filtered.map(task => { const node = nodes.find(n => n.id === task.node_id); return <div className="task-row" key={task.id}>
      <span>{node?.data.title || task.node_id.slice(0, 8)}<small>{new Date(task.created_at * 1000).toLocaleString()}</small></span>
      <span><i className={'status-dot ' + task.status}/>{task.error_code === 'REMOTE_RECONNECTING' && ['queued', 'running'].includes(task.status) ? '等待自动重连' : STATUS[task.status]}{task.reused ? ' · 缓存' : ''}</span><span className="task-error">{taskInformation(task)}</span>
      <span className="task-actions">{(task.output.text || task.output.assets?.length) && <button onClick={() => setPreviewId(task.id)}>查看结果</button>}
        {node && <button title="选中并定位到画布中的节点" onClick={() => useStudio.setState(s => ({ nodes: s.nodes.map(n => ({ ...n, selected: n.id === node.id })), focusRequest: { nodeId: node.id } }))}>选择节点</button>}
        {['queued', 'running'].includes(task.status) && <button onClick={() => cancel(task.id)}>取消</button>}
        {['failed', 'blocked', 'cancelled'].includes(task.status) && <button onClick={() => retry(task.id, task.error_code === 'SUBMIT_UNCERTAIN')}>重试</button>}</span>
    </div>; })}
    {!filtered.length && <p className="empty-line">{tasks.length ? '没有符合筛选条件的任务。' : '运行画布节点后，在这里查看任务状态。'}</p>}
    <dialog ref={dialog} className="task-result-dialog" aria-labelledby="task-result-title" onClose={() => setPreviewId('')}>
      {preview && <><header><h2 id="task-result-title">本次运行结果</h2><button autoFocus aria-label="关闭任务结果" onClick={() => dialog.current?.close()}>关闭</button></header>
        <p>{nodes.find(n => n.id === preview.node_id)?.data.title || preview.node_id} · {new Date(preview.created_at * 1000).toLocaleString()}</p>
        <small>仅查看这次任务的输出，不改变已采用版本。</small>
        {preview.output.text && <section><div className="result-text-actions"><h3>文本结果</h3><button disabled={copyState === '正在复制…'} onClick={() => void copyText(preview.output.text!)}>复制全文</button></div><p className="copy-feedback" role="status">{copyState}</p><pre tabIndex={0} aria-label="本次任务文本结果">{preview.output.text}</pre></section>}
        {preview.output.assets?.map(id => <MediaResult key={`${preview.id}:${id}`} asset={assets.find(a => a.id === id)}/>)}
      </>}
    </dialog>
  </div>;
}
