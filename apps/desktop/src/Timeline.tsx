import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Trash2, Volume2, VolumeX, Play, ListTodo, Clapperboard, Download, LoaderCircle } from 'lucide-react';
import { useStudio } from './store';
import { api, mediaUrl } from './api';
import { STATUS, type Clip, type ExportJob, type TimelineDoc } from './types';

import { TaskCenter } from './TaskCenter';
import { resizeTimeline } from './timelineLayout';

export function Timeline({ timeline, change, cancel, retry, exportVideo, exportJob, taskActivitySignal }: {
  timeline: TimelineDoc; change: (doc: TimelineDoc) => void; cancel: (id: string) => void; retry: (id: string, uncertain: boolean) => void; exportVideo: () => void; exportJob?: ExportJob; taskActivitySignal: number;
}) {
  const [tab, setTab] = useState('timeline'), [source, setSource] = useState<Clip>(), [subtitle, setSubtitle] = useState('');
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('canvas-bottom-collapsed') === 'true'; } catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem('canvas-bottom-collapsed', String(collapsed)); } catch { /* 存储不可用时仍可操作面板。 */ }
  }, [collapsed]);
  const [recentSubmission, setRecentSubmission] = useState(false);
  useEffect(() => {
    if (!taskActivitySignal) return;
    setRecentSubmission(true);
    const timer = window.setTimeout(() => setRecentSubmission(false), 1600);
    return () => window.clearTimeout(timer);
  }, [taskActivitySignal]);
  const [start, setStart] = useState(0), [end, setEnd] = useState(5), [playhead, setPlayhead] = useState(0);
  const [previewJob, setPreviewJob] = useState<ExportJob>(), [previewOpen, setPreviewOpen] = useState(false), [error, setError] = useState('');
  const [previewResolution, setPreviewResolution] = useState('');
  const video = useRef<HTMLVideoElement>(null), drag = useRef<string | null>(null), previewInput = useRef('');
  const tasks = useStudio(s => s.tasks), assets = useStudio(s => s.assets);
  let cursor = 0;
  const clips = timeline.clips.map(clip => {
    const startMs = clip.startMs ?? (clip.track === 'V2' ? 0 : cursor);
    if (clip.track !== 'V2') cursor = Math.max(cursor, startMs + clip.durationMs);
    return { ...clip, startMs, track: clip.track || 'V1' };
  });
  const total = Math.max(0, ...clips.map(clip => clip.startMs + clip.durationMs));
  const input = JSON.stringify({ ...timeline, version: undefined });
  const stale = !!previewJob && input !== previewInput.current;
  useEffect(() => {
    if (!previewJob || !['queued', 'running'].includes(previewJob.status)) return;
    const timer = setInterval(() => void api<ExportJob>(`/exports/${previewJob.id}`).then(setPreviewJob).catch(e => { setError(e.message); clearInterval(timer); }), 1000);
    return () => clearInterval(timer);
  }, [previewJob]);
  function patch(id: string, values: Partial<Clip>, audio = false) {
    const field = audio ? 'audio' : 'clips';
    change({ ...timeline, [field]: timeline[field].map(clip => clip.id === id ? { ...clip, ...values } : clip) });
  }
  function move(id: string, direction: number) {
    const ordered = timeline.clips.filter(clip => clip.track !== 'V2');
    const index = ordered.findIndex(clip => clip.id === id), target = index + direction;
    if (index < 0 || target < 0 || target >= ordered.length) return;
    const [clip] = ordered.splice(index, 1); ordered.splice(target, 0, clip);
    // 重新排序 V1 时恢复顺序排列，显式 V2 定位保持不变。
    let offset = 0;
    const sequential = ordered.map(item => { const value = { ...item, startMs: offset }; offset += item.durationMs; return value; });
    change({ ...timeline, clips: [...sequential, ...timeline.clips.filter(item => item.track === 'V2')] });
  }
  async function compose() {
    setError('');
    try {
      const pid = document.querySelector<HTMLSelectElement>('[aria-label="当前项目"]')?.value;
      if (!pid) return;
      // 等待 App 自动保存当前编辑，再从持久化快照生成实际合成预览。
      const deadline = Date.now() + 10000;
      while (Date.now() < deadline) {
        if (document.querySelector('.save-status')?.textContent?.includes('已保存到本机')) break;
        await new Promise(resolve => setTimeout(resolve, 250));
      }
      if (!document.querySelector('.save-status')?.textContent?.includes('已保存到本机')) {
        throw new Error('时间线尚未保存成功，请先保存项目后重新合成预览。');
      }
      const job = await api<ExportJob>(`/projects/${pid}/preview`, { method: 'POST' });
      if (job.id !== previewJob?.id) setPreviewResolution('');
      previewInput.current = input; setPreviewJob(job); setPreviewOpen(true);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  function numeric(clip: Clip, field: 'inMs' | 'durationMs' | 'startMs' | 'fadeInMs' | 'fadeOutMs', title: string, audio = false) {
    return <label>{title}<input aria-label={`${clip.title}${title}`} type="number" min={field === 'durationMs' ? 0.1 : 0} step={0.1} value={(clip[field] || 0) / 1000} onChange={e => patch(clip.id, { [field]: Math.max(field === 'durationMs' ? 100 : 0, Number(e.target.value) * 1000) }, audio)}/>s</label>;
  }
  function controls(clip: Clip, audio = false) {
    return <details className="clip-edit"><summary>裁切与混音</summary><div className="clip-fields">{numeric(clip, 'inMs', '源入点', audio)}{numeric(clip, 'durationMs', '时长', audio)}{numeric(clip, 'startMs', '起点', audio)}<label>音量<input aria-label={`${clip.title}音量`} type="number" min={0} max={2} step={0.1} value={clip.gain ?? 1} onChange={e => patch(clip.id, { gain: Math.min(2, Math.max(0, Number(e.target.value))) }, audio)}/></label>{numeric(clip, 'fadeInMs', '淡入', audio)}{numeric(clip, 'fadeOutMs', '淡出', audio)}</div>{!audio && <><label>适配<select aria-label={`${clip.title}画面适配`} value={clip.transform?.fit || 'contain'} onChange={e => patch(clip.id, { transform: { ...clip.transform, fit: e.target.value as 'contain' | 'cover' } })}><option value="contain">完整显示</option><option value="cover">裁切填满</option></select></label>{clip.track === 'V2' && <div className="clip-fields">{(['x', 'y', 'width', 'height'] as const).map(key => <label key={key}>{{ x: '横坐标', y: '纵坐标', width: '宽度', height: '高度' }[key]}<input aria-label={`${clip.title}${key}`} type="number" step={key === 'width' || key === 'height' ? 2 : 1} value={clip.transform?.[key] ?? (key === 'width' ? timeline.width : key === 'height' ? timeline.height : 0)} onChange={e => patch(clip.id, { transform: { ...clip.transform, [key]: Number(e.target.value) } })}/></label>)}</div>}</>}</details>;
  }
  const losslessEncoding = timeline.videoEncoding === 'lossless';
  const preserveSource = (timeline.exportMode || 'source') === 'source';
  const active = tasks.filter(task => ['queued', 'running', 'cancel_requested'].includes(task.status)).length;
  return <section id="bottom-panel" className={`bottom-panel${collapsed ? ' is-collapsed' : ''}`}>
    <div className="bottom-heading"><div className="tabs"><button className={tab === 'timeline' ? 'active' : ''} onClick={() => { setTab('timeline'); setCollapsed(false); }}><Clapperboard size={15}/>时间线</button><button className={[tab === 'tasks' ? 'active' : '', recentSubmission ? 'task-tab-notify' : ''].filter(Boolean).join(' ')} onClick={() => { setTab('tasks'); setCollapsed(false); }}><span key={taskActivitySignal} className={recentSubmission ? 'task-submission-flash' : undefined}>{active > 0 ? <LoaderCircle size={15} className="task-activity-spinner" aria-label="有任务正在处理"/> : <ListTodo size={15}/>}</span>任务中心 {active > 0 && <b>{active}</b>}</button></div><div className="timeline-meta" hidden={collapsed || tab !== 'timeline'}><span>{(total / 1000).toFixed(1)} s</span><label>导出模式<select aria-label="导出模式" value={timeline.exportMode || 'source'} onChange={e => change({ ...timeline, exportMode: e.target.value as 'source' | 'timeline' })}><option value="source">自动匹配原片画幅</option><option value="timeline">按时间线合成</option></select></label><label>视频编码<select aria-label="视频编码" value={timeline.videoEncoding || 'compatible'} onChange={e => change({ ...timeline, videoEncoding: e.target.value as 'compatible' | 'lossless' })}><option value="compatible">Windows 兼容（高画质）</option><option value="lossless">无损（需兼容播放器）</option></select></label><label>画幅<select disabled={preserveSource} aria-label="导出画幅" value={`${timeline.width}x${timeline.height}`} onChange={e => { const [width, height] = e.target.value.split('x').map(Number); change(resizeTimeline(timeline, width, height)); }}><option value="1080x1920">9:16 · 1080×1920</option><option value="1920x1080">16:9 · 1920×1080</option><option value="1080x1080">1:1 · 1080×1080</option></select></label><select disabled={preserveSource} aria-label="导出帧率" value={timeline.fps} onChange={e => change({ ...timeline, fps: Number(e.target.value) })}>{[24, 25, 30].map(fps => <option key={fps} value={fps}>{fps} fps</option>)}</select><button disabled={!clips.length || ['queued', 'running'].includes(previewJob?.status || '')} onClick={() => void compose()}><Play size={14}/>{['queued', 'running'].includes(previewJob?.status || '') ? '合成中…' : '合成预览'}</button><button onClick={exportVideo} disabled={!clips.length || ['queued', 'running'].includes(exportJob?.status || '')}><Download size={14}/>{exportJob?.status === 'running' ? '正在导出…' : '导出 MP4'}</button></div><button className="bottom-collapse" aria-label={collapsed ? "展开底部面板" : "收起底部面板"} aria-expanded={!collapsed} aria-controls="bottom-panel" onClick={() => setCollapsed(value => !value)}>{collapsed ? "展开" : "收起"}</button></div>
    {!collapsed && tab === 'timeline' && <small className="export-info">{preserveSource ? '按原片最大宽高统一尺寸，保留原帧率；同宽高比等比缩放填满，比例不同完整显示并留边。' : '按所选画幅与帧率合成；缩放、字幕等会改变画面。'} {losslessEncoding ? '无损编码保留缩放后的画面，文件较大，Windows 默认播放器可能无法播放。' : 'Windows 兼容 MP4 使用高质量压缩，保留渲染分辨率，非数学无损。'}</small>}
    {error && <p className="error-box" role="alert">{error}</p>}
    {exportJob && <div className={'export-info ' + (exportJob.status === 'failed' ? 'error-box' : '')}>{exportJob.status === 'completed' ? <a href={`/api/v1/exports/${exportJob.id}/content`} download>成片已完成，下载 MP4</a> : exportJob.error || '导出已排队，正在处理素材…'}</div>}
    {tab === 'tasks' ? <TaskCenter cancel={cancel} retry={retry}/> : <div className="timeline-scroll">
      <div className="timeline-ruler"><span>{(playhead / 1000).toFixed(2)} / {(total / 1000).toFixed(2)} s</span><input aria-label="播放头位置" type="range" min={0} max={total || 1} step={Math.round(1000 / timeline.fps)} value={playhead} onChange={e => { const value = Number(e.target.value); setPlayhead(value); if (video.current) video.current.currentTime = value / 1000; }}/></div>
      {(['V1', 'V2'] as const).map(track => <div className="track" key={track}><div className="track-label">{track}<span>{track === 'V1' ? '主镜头' : '叠加'}</span></div><div className="clips">{clips.filter(clip => clip.track === track).map((clip, i) => <article className="timeline-clip" key={clip.id} draggable onDragStart={() => { drag.current = clip.id; }} onDragOver={e => e.preventDefault()} onDrop={() => { if (drag.current && track === 'V1') { const source = clips.filter(c => c.track === 'V1').findIndex(c => c.id === drag.current); move(drag.current, i - source); } drag.current = null; }}><div><b>{String(i + 1).padStart(2, '0')}</b><strong>{clip.title}</strong><button aria-label="预览片段" onClick={() => setSource(clip)}><Play size={12}/></button></div><small>{(clip.startMs / 1000).toFixed(1)}–{((clip.startMs + clip.durationMs) / 1000).toFixed(1)} s</small>{controls(clip)}<footer>{track === 'V1' && <><button aria-label="前移镜头" onClick={() => move(clip.id, -1)}><ArrowLeft size={12}/></button><button aria-label="后移镜头" onClick={() => move(clip.id, 1)}><ArrowRight size={12}/></button></>}<button aria-label="切换镜头声音" onClick={() => patch(clip.id, { muted: !clip.muted })}>{clip.muted ? <VolumeX size={12}/> : <Volume2 size={12}/>}</button><button aria-label="切换视频轨" onClick={() => patch(clip.id, { track: track === 'V1' ? 'V2' : 'V1', startMs: track === 'V1' ? 0 : undefined })}>{track === 'V1' ? '叠加' : '主轨'}</button><button aria-label="移除镜头" onClick={() => change({ ...timeline, clips: timeline.clips.filter(c => c.id !== clip.id) })}><Trash2 size={12}/></button></footer></article>)}{track === 'V1' && !clips.length && <div className="track-empty">在视频节点中选择「批准并加入时间线」。</div>}{track === 'V2' && !clips.some(c => c.track === 'V2') && <div className="track-empty">将已批准片段切换到叠加轨，设置起点和画面位置。</div>}</div></div>)}
      {(['A1', 'A2'] as const).map(track => <div className="track audio-track" key={track}><div className="track-label">{track}<span>{track === 'A1' ? '对白' : '音乐 / 音效'}</span></div><div className="audio-clips">{timeline.audio.filter(clip => (clip.track || 'A1') === track).map(clip => <div className="audio-clip" key={clip.id}><span>{clip.title}</span>{controls(clip, true)}<button aria-label="切换音轨" onClick={() => patch(clip.id, { muted: !clip.muted }, true)}>{clip.muted ? <VolumeX size={12}/> : <Volume2 size={12}/>}</button><button aria-label="移除音轨" onClick={() => change({ ...timeline, audio: timeline.audio.filter(c => c.id !== clip.id) })}><Trash2 size={12}/></button></div>)}<select aria-label={track === 'A1' ? '添加配音或音乐' : '添加背景音乐'} value="" onChange={e => { const asset = assets.find(a => a.id === e.target.value); if (asset) change({ ...timeline, audio: [...timeline.audio, { id: crypto.randomUUID(), assetId: asset.id, title: asset.name, track, durationMs: total || 5000, inMs: 0, startMs: 0, gain: track === 'A2' ? 0.3 : 1 }] }); }}><option value="">＋ {track === 'A1' ? '添加配音' : '添加音乐 / 音效'}</option>{assets.filter(a => a.mime.startsWith('audio/')).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></div></div>)}
      <div className="track subtitle-track"><div className="track-label">S1<span>字幕</span></div><div className="subtitle-content"><div className="subtitle-entry"><input aria-label="字幕内容" placeholder="输入对白字幕" value={subtitle} onChange={e => setSubtitle(e.target.value)}/><input aria-label="字幕开始秒" type="number" min={0} value={start} onChange={e => setStart(Number(e.target.value))}/><span>—</span><input aria-label="字幕结束秒" type="number" min={0} value={end} onChange={e => setEnd(Number(e.target.value))}/><span>s</span><button disabled={!subtitle.trim() || end <= start || start < 0} onClick={() => { change({ ...timeline, subtitles: [...timeline.subtitles, { id: crypto.randomUUID(), text: subtitle.trim(), startMs: start * 1000, endMs: end * 1000 }] }); setSubtitle(''); }}>添加</button></div>{timeline.subtitles.map(sub => <span className="subtitle-chip" key={sub.id}>{sub.startMs / 1000}–{sub.endMs / 1000}s · {sub.text}<button aria-label="移除字幕" onClick={() => change({ ...timeline, subtitles: timeline.subtitles.filter(s => s.id !== sub.id) })}>×</button></span>)}</div></div>
    </div>}
    {source && <div className="modal-backdrop" onClick={() => setSource(undefined)}><div className="preview-dialog" onClick={e => e.stopPropagation()}><header><strong>源镜头 · {source.title}</strong><button onClick={() => setSource(undefined)}>关闭</button></header><video controls autoPlay src={mediaUrl(source.assetId)} onLoadedMetadata={e => { e.currentTarget.currentTime = source.inMs / 1000; }} onTimeUpdate={e => { if (e.currentTarget.currentTime >= (source.inMs + source.durationMs) / 1000) e.currentTarget.pause(); }}/><small>单素材预览。混音、叠加和字幕请使用「合成预览」。</small></div></div>}
    {previewOpen && previewJob && <div className="modal-backdrop" onClick={() => setPreviewOpen(false)}><div className="preview-dialog" onClick={e => e.stopPropagation()}><header><strong>时间线合成预览</strong><button onClick={() => setPreviewOpen(false)}>关闭</button></header>{previewJob.status === 'completed' ? <><video ref={video} controls autoPlay src={`/api/v1/exports/${previewJob.id}/content`} onLoadedMetadata={e => { e.currentTarget.currentTime = playhead / 1000; setPreviewResolution(e.currentTarget.videoWidth + '×' + e.currentTarget.videoHeight); }} onTimeUpdate={e => setPlayhead(Math.round(e.currentTarget.currentTime * 1000))}/><small>{stale ? '时间线已修改，请重新合成预览。' : '已按成片分辨率' + (previewResolution ? '（' + previewResolution + '）' : '') + '合成；预览使用兼容播放编码，正式导出按所选视频编码生成。'}</small>{stale && <button onClick={() => void compose()}>重新合成</button>}</> : <p className={previewJob.status === 'failed' ? 'error-box' : ''}>{previewJob.error || '正在合成当前时间线…'}</p>}</div></div>}
  </section>;
}
