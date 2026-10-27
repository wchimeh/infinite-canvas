import { useLayoutEffect, useRef, useState } from 'react';
import { AudioLines, Check, FileText, Film, Image } from 'lucide-react';
import { thumbnailUrl } from './api';
import type { InputCandidate } from './inputCandidates';

const ROW_HEIGHT = 72, WINDOW_HEIGHT = 288, BUFFER = 2;

function CandidatePreview({ candidate }: { candidate: InputCandidate }) {
  const [failed, setFailed] = useState(false);
  const Icon = candidate.type === 'image' ? Image : candidate.type === 'audio' ? AudioLines : candidate.type === 'video' ? Film : FileText;
  return <span className="input-picker-preview">{['image', 'video'].includes(candidate.type) && candidate.asset && !failed
    ? <img src={thumbnailUrl(candidate.asset.id)} alt="" loading="lazy" decoding="async" onError={() => setFailed(true)}/>
    : <Icon size={22} aria-hidden="true"/>}</span>;
}

export function InputCandidateList({ candidates, typeName, emptyText, onSelect }: {
  candidates: InputCandidate[]; typeName: string; emptyText: string; onSelect: (candidate: InputCandidate) => void;
}) {
  const list = useRef<HTMLDivElement>(null);
  const [first, setFirst] = useState(0);
  const [focusIndex, setFocusIndex] = useState<number | null>(null);
  const start = Math.max(0, Math.min(first, Math.max(0, candidates.length - 1)) - BUFFER);
  const end = Math.min(candidates.length, first + Math.ceil(WINDOW_HEIGHT / ROW_HEIGHT) + BUFFER + 1);
  useLayoutEffect(() => {
    if (focusIndex === null) return;
    list.current?.querySelector<HTMLButtonElement>(`[data-candidate-index="${focusIndex}"]`)?.focus({ preventScroll: true });
    setFocusIndex(null);
  }, [focusIndex, start, end]);
  return <div ref={list} className="input-picker-list" style={candidates.length ? { height: Math.min(WINDOW_HEIGHT, candidates.length * ROW_HEIGHT) + 6 } : undefined}
    onScroll={event => setFirst(Math.floor(event.currentTarget.scrollTop / ROW_HEIGHT))}
    onKeyDown={event => {
      if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
      const current = Number((event.target as HTMLElement).closest<HTMLButtonElement>('[data-candidate-index]')?.dataset.candidateIndex);
      if (!Number.isFinite(current)) return;
      event.preventDefault(); event.stopPropagation();
      const direction = event.key === 'ArrowUp' || event.key === 'End' ? -1 : 1;
      let next = event.key === 'Home' ? 0 : event.key === 'End' ? candidates.length - 1 : current + direction;
      while (next >= 0 && next < candidates.length && candidates[next].connected) next += direction;
      if (next < 0 || next >= candidates.length) return;
      const element = list.current!;
      if (next * ROW_HEIGHT < element.scrollTop) element.scrollTop = next * ROW_HEIGHT;
      else if ((next + 1) * ROW_HEIGHT > element.scrollTop + element.clientHeight - 6) element.scrollTop = (next + 1) * ROW_HEIGHT - element.clientHeight + 6;
      setFirst(Math.floor(element.scrollTop / ROW_HEIGHT)); setFocusIndex(next);
    }}>
    {candidates.length ? <div className="input-picker-virtual" style={{ height: candidates.length * ROW_HEIGHT }}>
      {candidates.slice(start, end).map((candidate, offset) => <button key={`${candidate.source}:${candidate.sourceHandle}`} data-candidate-index={start + offset}
        className="input-picker-option" style={{ transform: `translateY(${(start + offset) * ROW_HEIGHT}px)` }} disabled={candidate.connected}
        aria-label={`${candidate.connected ? '已连接' : '连接'}：${candidate.title}`} onClick={() => onSelect(candidate)}>
        <CandidatePreview key={candidate.asset?.id || 'empty'} candidate={candidate}/>
        <span className="input-picker-copy"><strong>{candidate.title}</strong><small>{candidate.summary || candidate.asset?.name || '尚无预览 · 可连接为上游'}</small></span>
        {candidate.connected ? <span className="input-picker-connected"><Check size={14}/>已连接</span> : <span className="input-picker-kind">{typeName}</span>}
      </button>)}
    </div> : <p className="input-picker-empty">{emptyText}</p>}
  </div>;
}
