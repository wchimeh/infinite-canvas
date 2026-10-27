## 开发文档：武打节点 transition_step 可配置化

### 背景
SelfLift 采样节点的 transition_step 目前由后端按 `min(6, steps-1)` 自动计算，用户无法调整；同时采样步数默认值需恢复为与工作流模板一致的 10 步。

### 目标
- [x] 节点 397 的 transition_step 暴露为用户可配置参数，默认值 6。
- [x] 节点 261 的 steps 默认值恢复为 10。
- [x] 超范围配置（transition_step ≥ steps）在提交云端前被明确拒绝，不产生费用。

### 涉及文件
| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `services/backend/app/combat_video_workflow.py` | 修改 | steps 默认 10；transition_step 改为可配置并校验 1–(steps-1) |
| `apps/desktop/src/CombatVideoSettings.tsx` | 修改 | 新增切换步数输入项；steps 默认显示 10；steps 变小时自动钳制 transitionStep |
| `services/backend/app/generation_profiles.py` | 修改 | combat 内置工作流 version 2 → 3 |
| `services/backend/tests/test_combat_video.py` | 修改 | 默认值、边界、版本号断言更新 |

### 任务清单（必须全部标记完成）
- [x] 任务 1：后端适配。输入 `combatH3.steps`（默认 10）与 `combatH3.transitionStep`（默认 6，整数），输出 261.steps 与 397.transition_step；transitionStep 超出 1–(steps-1) 时抛出 ValueError。
- [x] 任务 2：后端版本号。combat 内置工作流 version 升为 3，使新任务不复用 version 2 的参数缓存。
- [x] 任务 3：前端设置项。新增"SelfLift切换步数"输入（默认 6，min 1，max 当前 steps-1）；steps 默认显示 10；修改 steps 时若已有 transitionStep 超界则一并钳制；更新底部说明文案。
- [x] 任务 4：回归测试。先写失败测试再实现：默认 steps=10 且 transition_step=6；steps=6 时默认 transition_step=6 被拒绝；显式合法组合通过；非法 transitionStep（0、≥steps、非整数）报错；version==3 断言更新。
- [x] 任务 5：验证。后端 `pytest tests/test_combat_video.py` 全绿，前端 `pnpm build` 通过。

### 验收标准
- [x] 默认配置构建出 261.steps=10、397.transition_step=6。
- [x] transition_step=steps 的请求在本地校验阶段报错，不提交云端。
- [x] 显式设置的合法 steps/transitionStep 组合原样透传，不被改写。
- [x] 已有任务与缓存行为不受影响（version 3 快照与旧缓存区分）。

### 风险点
- transition_step 的上限依赖 steps，校验顺序必须先 steps 后 transitionStep。
- UI 中先存了较大的 transitionStep 再调小 steps，会出现存储值暂时非法：UI 在修改 steps 时同步钳制，后端兜底报错。
- version 升级后，旧的 version 2 已完成任务不受影响，仅影响新生成任务的缓存匹配。
