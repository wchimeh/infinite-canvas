import { useEffect, useState } from 'react';
import { api } from './api';

type Queue = { id: 'text' | 'media' | 'audio'; capacity: number; occupied: number; waiting: number };
const names = { text: 'LLM 文本', media: '图片＋视频', audio: '音频' };

export function QueueSummary() {
  const [queues, setQueues] = useState<Queue[]>();
  const [error, setError] = useState('');
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const data = await api<{ queues: Queue[] }>('/queues');
        if (!stopped) { setQueues(data.queues); setError(''); }
      } catch {
        if (!stopped) setError('队列状态更新失败，正在重试');
      } finally {
        if (!stopped) timer = setTimeout(() => void refresh(), 2000);
      }
    }
    void refresh();
    return () => { stopped = true; clearTimeout(timer); };
  }, []);
  return <section className="queue-summary" aria-label="全局队列概览">
    <div className="queue-summary-items">{queues?.map(queue => <div key={queue.id}>
      <strong>{names[queue.id]}</strong><span>占用 {queue.occupied} / {queue.capacity}</span><span>待调度 {queue.waiting}</span>
      {queue.occupied >= queue.capacity && <small>{queue.occupied > queue.capacity ? '等待已有任务释放名额' : '并发已满'}</small>}
    </div>)}</div>
    {error ? <small role="status">{error}；当前数字可能已过期。</small> : !queues ? <small>正在读取队列状态…</small> : null}
    <small>所有项目合计 · 角色图逐张生成 · 云端排队也占用名额 · 待调度包含等待上游的任务 · 上限在设置 → 费用与并发中修改</small>
  </section>;
}
