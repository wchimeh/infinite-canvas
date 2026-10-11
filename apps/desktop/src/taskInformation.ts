import type { Task } from './types';

export function taskInformation(task: Task): string {
  if (task.error) return task.error;
  switch (task.status) {
    case 'completed': {
      if (task.snapshot?.kind === 'story.prompt') return '已输出故事原文，未调用大模型；生成新文本请运行“剧本扩写”节点';
      const results = [];
      if (task.output.text) results.push('文本结果');
      if (task.output.assets?.length) results.push(`${task.output.assets.length} 个素材结果`);
      return `${task.reused ? '已复用缓存结果' : '任务已完成'}${results.length ? ' · ' + results.join('、') : ''}；选中对应节点查看`;
    }
    case 'queued': return task.external_id ? '已提交云端，等待服务处理' : task.snapshot?.kind === 'image.character' && !('adopted' in task.snapshot && task.snapshot.adopted) ? '角色图逐张生成，等待本地调度' : '等待本地调度';
    case 'running': return task.external_id ? '云端任务处理中，正在查询结果' : '任务执行中，请稍候';
    case 'blocked': return '上游任务未完成，请先检查依赖节点';
    case 'failed': return '任务执行失败，请检查节点配置或重试';
    case 'cancel_requested': return '正在处理取消请求，云端任务可能继续运行';
    case 'cancelled': return '任务已取消';
    default: return '任务状态待更新';
  }
}
