import { useState } from 'react';
import { mediaUrl, downloadUrl } from './api';
import type { Asset } from './types';

export function MediaResult({ asset }: { asset?: Asset }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  if (!asset) return <section><h3>素材已不存在</h3><p>此结果素材已被删除，无法预览。</p></section>;
  const image = asset.mime.startsWith('image/'), video = asset.mime.startsWith('video/'), audio = asset.mime.startsWith('audio/');
  const supported = image || video || audio;
  const original = mediaUrl(asset.id);
  const src = attempt ? `${original}?previewRetry=${attempt}` : original;
  const ready = () => setState('ready'), failed = () => setState('error');
  return <section className="media-result" aria-label={`媒体结果：${asset.name}`}>
    <div className="media-result-heading"><h3>{asset.name}</h3><a href={downloadUrl(asset.id)} download={asset.name}>下载原文件</a></div>
    {supported && state === 'loading' && <p className="media-result-status" role="status">正在加载预览…</p>}
    {supported && state === 'error' ? <div className="media-result-error" role="alert"><p>预览加载失败，可能是文件暂时不可用或浏览器不支持此格式。可重新加载，或下载原文件查看。</p><button onClick={() => { setState('loading'); setAttempt(value => value + 1); }}>重新加载</button><small>仅重新读取素材，不会重新生成。</small></div> :
      image ? <img key={attempt} src={src} alt={asset.name} onLoad={ready} onError={failed}/> :
      video ? <video key={attempt} src={src} controls preload="metadata" onLoadedMetadata={ready} onError={failed}/> :
      audio ? <audio key={attempt} src={src} controls preload="metadata" onLoadedMetadata={ready} onError={failed}/> :
      <p>此格式暂不支持预览，可下载原文件查看。</p>}
  </section>;
}
