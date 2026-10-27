import { useEffect, useState } from 'react';
import type { Config } from './types';

type Options = { aspectRatio?: string; megapixels?: number; multiple?: number; steps?: number; seedMode?: 'random' | 'fixed'; seed?: number };
const ratios = ['1:1 (Square)', '2:3 (Portrait Photo)', '3:2 (Photo)', '3:4 (Portrait Standard)', '4:3 (Standard)', '9:16 (Portrait Widescreen)', '16:9 (Widescreen)', '21:9 (Ultrawide)'];

function Parameter({ label, value, min, max, step, onChange }: { label: string; value: number; min: number; max: number; step: number; onChange: (value: number) => void }) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  const commit = () => {
    const parsed = Number(draft);
    const next = draft.trim() && Number.isFinite(parsed) && parsed >= min && parsed <= max && (step !== 1 || Number.isInteger(parsed)) ? parsed : value;
    setDraft(String(next));
    if (next !== value) onChange(next);
  };
  return <label>{label}<input aria-label={label} type="number" min={min} max={max} step={step} value={draft}
    onChange={e => setDraft(e.target.value)} onBlur={commit} onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur(); }}/></label>;
}

export function MiniMaxSettings({ config, patch, disabled }: { config: Config; patch: (value: Partial<Config>) => void; disabled: boolean }) {
  const options: Options = config.minimaxH3 && typeof config.minimaxH3 === 'object' ? config.minimaxH3 as Options : {};
  const update = (value: Partial<Options>) => patch({ minimaxH3: { ...options, ...value } });
  const ratio = options.aspectRatio ?? '16:9 (Widescreen)';
  return <fieldset className="generation-choice" disabled={disabled}>
    <legend>MiniMax H3 生成参数</legend>
    <label>画面比例<select aria-label="画面比例" value={ratio} onChange={e => update({ aspectRatio: e.target.value })}>
      {!ratios.includes(ratio) && <option value={ratio} disabled>无效比例，请重新选择</option>}
      {ratios.map(value => <option key={value} value={value}>{value}</option>)}
    </select></label>
    <div className="field-row">
      <Parameter label="百万像素（MP）" value={options.megapixels ?? 0.4} min={0.01} max={16} step={0.01} onChange={megapixels => update({ megapixels })}/>
      <Parameter label="尺寸倍数" value={options.multiple ?? 32} min={1} max={1024} step={1} onChange={multiple => update({ multiple })}/>
    </div>
    <Parameter label="采样步数" value={options.steps ?? 8} min={1} max={1000} step={1} onChange={steps => update({ steps })}/>
    <label>种子模式<select aria-label="种子模式" value={options.seedMode ?? 'random'} onChange={e => update({ seedMode: e.target.value as Options['seedMode'], seed: options.seed ?? 0 })}>
      <option value="random">随机（每次提交重新取值）</option><option value="fixed">固定种子</option>
    </select></label>
    {options.seedMode === 'fixed' && <Parameter label="固定种子" value={options.seed ?? 0} min={0} max={2147483646} step={1} onChange={seed => update({ seed })}/>}
    <small>参数仅用于此节点。随机模式复用缓存时不会重新取值，点击“重新生成”可重新提交。</small>
  </fieldset>;
}
