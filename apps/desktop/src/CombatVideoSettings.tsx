import { useEffect, useState } from 'react';
import type { Config } from './types';

type Options = { aspectRatio?: string; megapixels?: number; steps?: number; transitionStep?: number; cfg?: number; seedMode?: 'random' | 'fixed'; seed?: number;
  combatStrength?: number; motionRepairStrength?: number; fightFlowStrength?: number; speedStrength?: number };
const ratios = ['1:1 (Square)', '2:3 (Portrait Photo)', '3:2 (Photo)', '3:4 (Portrait Standard)', '4:3 (Standard)', '9:16 (Portrait Widescreen)', '16:9 (Widescreen)', '21:9 (Ultrawide)'];

function Parameter({ label, value, min, max, step, change }: { label: string; value: number; min: number; max: number; step: number; change: (value: number) => void }) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  const commit = () => {
    const parsed = Number(draft);
    const next = draft.trim() && Number.isFinite(parsed) && parsed >= min && parsed <= max && (step !== 1 || Number.isInteger(parsed)) ? parsed : value;
    setDraft(String(next)); if (next !== value) change(next);
  };
  return <label>{label}<input aria-label={label} type="number" value={draft} min={min} max={max} step={step}
    onChange={e => setDraft(e.target.value)} onBlur={commit} onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur(); }}/></label>;
}

export function CombatVideoSettings({ config, patch, disabled }: { config: Config; patch: (value: Partial<Config>) => void; disabled: boolean }) {
  const options: Options = config.combatH3 && typeof config.combatH3 === 'object' ? config.combatH3 as Options : {};
  const update = (value: Partial<Options>) => patch({ combatH3: { ...options, ...value } });
  const steps = options.steps ?? 10;
  const transitionStep = Math.min(options.transitionStep ?? 6, steps - 1);
  return <fieldset className="generation-choice" disabled={disabled}>
    <legend>文武05 · 生成参数</legend>
    <label>画面比例<select aria-label="武打画面比例" value={options.aspectRatio ?? '16:9 (Widescreen)'} onChange={e => update({ aspectRatio: e.target.value })}>
      {ratios.map(ratio => <option key={ratio}>{ratio}</option>)}
    </select></label>
    <div className="field-row">
      <Parameter label="武打分辨率（MP）" value={options.megapixels ?? 0.5} min={0.01} max={16} step={0.01} change={megapixels => update({ megapixels })}/>
      <Parameter label="武打采样步数" value={steps} min={2} max={1000} step={1}
        change={next => update((options.transitionStep ?? 6) > next - 1 ? { steps: next, transitionStep: next - 1 } : { steps: next })}/>
    </div>
    <div className="field-row">
      <Parameter label="提示词引导（CFG）" value={options.cfg ?? 1} min={0} max={20} step={0.1} change={cfg => update({ cfg })}/>
      <Parameter label="SelfLift切换步数" value={transitionStep} min={1} max={steps - 1} step={1} change={transitionStep => update({ transitionStep })}/>
    </div>
    <div className="field-row">
      <Parameter label="武打强度" value={options.combatStrength ?? 0.35} min={0} max={2} step={0.05} change={combatStrength => update({ combatStrength })}/>
      <Parameter label="动作修复强度" value={options.motionRepairStrength ?? 0.35} min={0} max={2} step={0.05} change={motionRepairStrength => update({ motionRepairStrength })}/>
    </div>
    <div className="field-row">
      <Parameter label="动作连贯强度" value={options.fightFlowStrength ?? 0.35} min={0} max={2} step={0.05} change={fightFlowStrength => update({ fightFlowStrength })}/>
      <Parameter label="速度强度" value={options.speedStrength ?? 1} min={0} max={4} step={0.1} change={speedStrength => update({ speedStrength })}/>
    </div>
    <label>种子模式<select aria-label="武打种子模式" value={options.seedMode ?? 'random'} onChange={e => update({ seedMode: e.target.value as Options['seedMode'] })}>
      <option value="random">随机</option><option value="fixed">固定种子</option>
    </select></label>
    {options.seedMode === 'fixed' && <Parameter label="武打固定种子" value={options.seed ?? 0} min={0} max={Number.MAX_SAFE_INTEGER} step={1} change={seed => update({ seed })}/>}
    <small>默认10步、切换步数6、速度1、武打0.35。SelfLift切换步数须小于采样步数（采样最少2步），调小步数时切换步数会自动跟随下调。强度控制对应动作 LoRA；设为0可关闭该项。固定种子用于对比，随机模式在重新提交时更新。</small>
  </fieldset>;
}
