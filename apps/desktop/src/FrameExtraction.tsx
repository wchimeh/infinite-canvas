import { useEffect, useRef, useState } from 'react';
import { mediaUrl } from './api';
import { useStudio } from './store';

export function FrameExtraction({ nodeId, busy, run }: { nodeId: string; busy: boolean; run: (ids: string[], force?: boolean) => void }) {
  const s = useStudio();
  const node = s.nodes.find(n => n.id === nodeId)!;
  const edge = s.edges.find(e => e.target === nodeId && e.targetHandle === 'video' && e.data?.kind !== 'sequence');
  const source = s.nodes.find(n => n.id === edge?.source);
  const task = s.tasks.filter(t => t.node_id === source?.id).sort((a, b) => b.created_at - a.created_at)[0];
  const assetId = source?.data.config.assetId || (source?.data.status !== 'dirty' && task?.status === 'completed' ? task.output.assets?.[0] : undefined);
  const asset = s.assets.find(a => a.id === assetId && a.mime.startsWith('video/'));
  const time = node.data.config.frameTime ?? 0;
  const patch = (value: number) => {
    if (value !== time) s.patch(nodeId, { config: { ...node.data.config, frameTime: value, assetId: undefined } });
  };
  return <section className="inspector-section" aria-label="视频选帧">
    <h3>选择视频画面</h3>
    {asset ? <FramePreview key={`${nodeId}:${asset.id}`} assetId={asset.id} time={time} patch={patch} busy={busy} capture={force => run([nodeId], force)}/> : <>
      <p className="muted">{edge ? '上游视频尚未就绪，请先运行上游视频节点或选择已采用的视频。' : '请将视频素材或生成视频节点的输出连接到此节点。'}</p>
      <button disabled={busy || !edge} onClick={() => run([nodeId])}>运行上游并截帧</button>
    </>}
    <small>拖动进度条定位，点击截取后输出原分辨率 PNG 图片。仅在本地处理，不产生云端费用；生成上游视频的费用另计。时间位置会随项目保存，视频末尾截取最后一帧。</small>
  </section>;
}

function FramePreview({ assetId, time, patch, busy, capture }: { assetId: string; time: number; patch: (time: number) => void; busy: boolean; capture: (force: boolean) => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(false);
  const [seeking, setSeeking] = useState(false);
  const invalid = !Number.isFinite(time) || time < 0 || (duration > 0 && time > duration);
  useEffect(() => {
    if (!video.current || !duration || invalid || Math.abs(video.current.currentTime - time) < .0001) return;
    video.current.pause();
    video.current.currentTime = time;
  }, [time, duration, invalid]);
  return <>
    <video ref={video} src={mediaUrl(assetId)} preload="auto" muted playsInline aria-label="截帧视频预览"
      style={{ width: '100%', maxHeight: 280, objectFit: 'contain', borderRadius: 8, background: '#111' }}
      onLoadedMetadata={e => { const value = e.currentTarget.duration; if (Number.isFinite(value) && value > 0) setDuration(value); else setError(true); }}
      onSeeking={() => setSeeking(true)} onSeeked={() => setSeeking(false)} onError={() => { setError(true); setSeeking(false); }}/>
    {error ? <p role="alert">视频无法预览，可能不支持此编码。仍可填写时间并在本地截帧，或转换为 MP4 后重试。</p> : !duration ? <p role="status">正在加载视频…</p> : null}
    <fieldset disabled={busy}>
      <legend>截帧位置</legend>
      <input aria-label="截帧进度" type="range" min={0} max={duration || 1} step="0.001" value={Math.min(Math.max(time || 0, 0), duration || 1)} disabled={!duration || error}
        style={{ width: '100%' }} onChange={e => patch(Number(e.target.value))}/>
      <label>截帧时间（秒）<input aria-label="截帧时间（秒）" type="number" min={0} max={duration || undefined} step="0.001" value={time} onChange={e => patch(e.target.value === '' ? 0 : Number(e.target.value))}/></label>
      {duration > 0 && <small>当前 {time.toFixed(3)} 秒 / 共 {duration.toFixed(3)} 秒</small>}
      {invalid && <p role="alert">请选择视频时长范围内的有效时间。</p>}
      <div className="field-row">
        <button className="primary" disabled={invalid || seeking || (!duration && !error)} onClick={() => capture(false)}>截取当前帧</button>
        <button disabled={invalid || seeking || (!duration && !error)} onClick={() => capture(true)}>重新截取</button>
      </div>
    </fieldset>
  </>;
}
