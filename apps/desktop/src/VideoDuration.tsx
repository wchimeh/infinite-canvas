import { useEffect, useState } from 'react';

export function VideoDuration({ seconds, onChange }: { seconds?: number; onChange: (seconds: number) => void }) {
  const value = seconds ?? 5;
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  const commit = () => {
    const parsed = Number(draft);
    const next = draft.trim() && Number.isFinite(parsed) ? Math.min(30, Math.max(1, parsed)) : value;
    setDraft(String(next));
    if (next !== value) onChange(next);
  };
  return <label className="video-duration nodrag nowheel"><span className="video-duration-label">生成时长</span><span className="video-duration-control"><input aria-label="生成时长（秒）" type="number" min={1} max={30} step="any" value={draft}
    onChange={event => setDraft(event.target.value)} onBlur={commit}
    onKeyDown={event => { event.stopPropagation(); if (event.key === 'Enter') event.currentTarget.blur(); }}/><span className="video-duration-unit" aria-hidden="true">秒</span></span></label>;
}
