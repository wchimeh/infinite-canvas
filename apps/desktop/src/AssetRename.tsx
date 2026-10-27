import { useState } from 'react';

export function AssetRename({ name, rename }: { name: string; rename: (name: string) => Promise<void> }) {
  const [editing, setEditing] = useState(false), [draft, setDraft] = useState(name);
  const [saving, setSaving] = useState(false), [error, setError] = useState('');
  if (!editing) return <button aria-label={`重命名${name}`} onClick={() => { setDraft(name); setError(''); setEditing(true); }}>重命名</button>;
  return <form className="asset-rename" onKeyDown={e => { if (e.key === 'Escape') { e.stopPropagation(); if (!saving) setEditing(false); } }} onSubmit={async e => {
    e.preventDefault(); if (saving || !draft.trim()) return;
    setSaving(true); setError('');
    try { await rename(draft.trim()); setEditing(false); }
    catch (e) { setError(e instanceof Error ? e.message : '重命名失败，请重试'); }
    finally { setSaving(false); }
  }}>
    <label>素材名称<input autoFocus aria-label="素材名称" maxLength={200} value={draft} disabled={saving} onFocus={e => e.target.select()} onChange={e => setDraft(e.target.value)}/></label>
    <div><button type="submit" disabled={saving || !draft.trim()}>{saving ? '保存中…' : '保存名称'}</button><button type="button" disabled={saving} onClick={() => setEditing(false)}>取消</button></div>
    {error && <small role="alert">{error}</small>}
  </form>;
}
