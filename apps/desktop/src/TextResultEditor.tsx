import { useState } from 'react';
import { api } from './api';
import { useStudio } from './store';
import type { EditedTextResult } from './types';

export function TextResultEditor({ nodeId, taskId, output, busy }: { nodeId: string; taskId: string; output: EditedTextResult; busy: boolean }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(output.text);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const node = useStudio(s => s.nodes.find(n => n.id === nodeId));
  const edited = !!node?.data.config.editedResult;
  async function save() {
    if (!node) return;
    const captured = node;
    setSaving(true); setError('');
    try {
      const result = await api<EditedTextResult>(`/tasks/${taskId}/text-preview`, { method: 'POST', body: JSON.stringify({ text: draft }) });
      const state = useStudio.getState();
      if (state.nodes.find(n => n.id === nodeId) !== captured) throw new Error('节点已变化，请重新打开编辑后保存');
      state.patch(nodeId, { config: { ...captured.data.config, editedResult: result,
        originalResult: captured.data.config.editedResult ? captured.data.config.originalResult : output } });
      setEditing(false);
    } catch (e) { setError(e instanceof Error ? e.message : '保存失败'); }
    finally { setSaving(false); }
  }
  function restore() {
    const current = useStudio.getState().nodes.find(n => n.id === nodeId);
    if (current) useStudio.getState().patch(nodeId, { config: { ...current.data.config, editedResult: undefined } });
    setError('');
  }
  return <section className="result-section">
    <h3>文本结果{edited ? ' · 已编辑' : ''}</h3>
    {editing ? <>
      <label>编辑生成结果<textarea aria-label="编辑生成结果" rows={16} value={draft} disabled={saving || busy} onChange={e => setDraft(e.target.value)}/></label>
      <small>角色、场景和分镜请保留 JSON 数组及字段名。保存时会检查格式；已排队任务不受修改影响。</small>
      <div className="button-row"><button disabled={saving || busy || !draft.trim()} onClick={save}>{saving ? '校验中…' : '保存修改'}</button><button disabled={saving} onClick={() => { setEditing(false); setError(''); }}>取消</button></div>
    </> : <>
      <pre>{output.text}</pre>
      <div className="button-row"><button disabled={busy} onClick={() => { setDraft(output.text); setEditing(true); setError(''); }}>编辑结果</button>{edited && <button disabled={busy} onClick={restore}>恢复生成结果</button>}</div>
    </>}
    {edited && <p className="muted">下游将使用修改稿。运行本节点也采用修改稿，不调用模型；如需重新生成，请先恢复生成结果。修改稿随项目保存。</p>}
    {error && <p role="alert">{error}</p>}
  </section>;
}
