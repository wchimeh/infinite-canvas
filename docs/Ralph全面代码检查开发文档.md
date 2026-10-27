## 开发文档：Ralph 全面代码检查与优化

### 背景
按用户指定的 ralph-wiggum-codex 技能执行全仓库检查、修复和独立上下文复审。

### 目标
- [x] 审查前端状态与交互、后端 API/存储/队列/缓存、生成适配、导出与桌面脚本。
- [x] 修复有证据的高优先级问题，保留已有改动，避免无依据重构。
- [x] 完成验证和独立复审，记录实际边界，不以测试通过替代成片质量。

### 涉及文件
| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `.codex/ralph-loop/` | 新建（本地运行状态） | 目标、验收、工作和复审交接 |
| `docs/Ralph全面代码检查开发文档.md` | 新建/更新 | 最小执行任务与验收证据 |
| `apps/desktop/src/api.ts` | 修改 | 启动令牌读取后立即移出地址栏 |
| `apps/desktop/src/api.test.mjs` | 新建 | 隔离验证启动会话成功/失败路径均不残留 token |
| `apps/desktop/src/App.tsx` | 修改 | 分别修复项目切换竞态、多参考图生成输入 |
| `apps/desktop/src/projectLoad.ts` | 新建 | 封装“仅最新项目加载可提交”的请求序号门禁 |
| `apps/desktop/src/projectLoad.test.mjs` | 新建 | 以逆序响应验证旧项目加载结果失效 |
| `apps/desktop/src/shotReferences.ts` | 新建 | 纯函数收集并校验分镜人物/场景参考图 |
| `apps/desktop/src/shotReferences.test.mjs` | 新建 | 覆盖参考图顺序、去重与已删除素材过滤 |
| `scripts/smoke.mjs` | 修改 | 禁止默认连接日常会话执行真实写入验收 |
| `scripts/performance.mjs` | 修改 | 禁止默认把性能项目写入日常数据根 |
| 对应测试文件 | 修改/新建 | 为每项确定性修复补回归验证 |

### 任务清单（必须全部标记完成）
- [x] 任务 1：建立目标、验收、反馈和基线，运行技能的工作/复审循环；Windows 必要兼容仅限本地脚本副本。
- [x] 任务 2：只读审查各模块并记录按严重度排序的问题，明确证据和影响。
- [x] 任务 3：将确认的问题逐项拆为单文件/单逻辑任务，先写文档，再依序修复、验证和勾选。
- [x] 任务 3.1：修改 `apps/desktop/src/api.ts` 的启动会话逻辑。输入：URL fragment 中的一次性 token；输出：读取后立即清除 fragment，再向 `/session` 提交，失败页面和浏览器历史均不保留 token；验证：会话成功与失败回归均检查地址栏不含 token。
  - [x] 任务 3.1.1：新建 `apps/desktop/src/api.test.mjs`，输入为隔离的 URL/history/fetch 替身，输出为成功与失败路径的 token 清理断言；验证方法：先运行 `pnpm --filter desktop exec node --test src/api.test.mjs` 并确认失败路径稳定红灯。证据：修复前 2 项均因 fetch 观察到 `#token=one-time-secret` 而失败。
  - [x] 任务 3.1.2：修改 `apps/desktop/src/api.ts` 中的单一 token 清理时序，输入为 fragment token，输出为发起会话请求前已替换当前历史项；验证方法：同一定向测试全部通过。证据：修复后成功/失败 2 项均通过，且 fetch 观察到的 fragment 均为空。
- [x] 任务 3.2：修改 `apps/desktop/src/App.tsx` 的项目切换逻辑。输入：用户快速连续选择项目 A、B；输出：仅最新请求可加载，切换期间禁止用旧项目状态继续编辑；验证：构造逆序响应，最终项目和画布必须为 B，且旧响应不能覆盖。
  - [x] 任务 3.2.1：新建 `apps/desktop/src/projectLoad.test.mjs`。输入：A、B 两次加载及可控的逆序响应；输出：B 可提交、A 被判定为过期，开始切换时立即进入不可编辑态；验证方法：运行 `pnpm --filter desktop exec node --test src/projectLoad.test.mjs`，先确认因门禁模块不存在而稳定红灯。证据：测试以 `ERR_MODULE_NOT_FOUND`、退出码 1 失败，确认生产门禁尚不存在。
  - [x] 任务 3.2.2：新建 `apps/desktop/src/projectLoad.ts`。输入：每次项目切换开始信号；输出：单调请求序号及最新性判断；验证方法：3.2.1 定向测试通过。证据：逆序响应测试 1 项通过，B 提交后 A 无法覆盖。
  - [x] 任务 3.2.3：修改 `apps/desktop/src/App.tsx` 的项目加载提交点。输入：门禁序号和五类项目响应；输出：切换开始即清空当前项目标识，只有最新序号提交项目、画布、素材、时间线和人物状态；验证方法：desktop 类型检查通过，并由 3.2.1 的逆序模型覆盖提交规则。证据：定向测试 1 项通过，`pnpm --filter desktop typecheck` 退出码 0；过期成功响应和过期错误均不再提交或打扰当前项目。
- [x] 任务 3.3：修改 `apps/desktop/src/App.tsx` 的分镜参考图收集逻辑。输入：人物/场景 Profile 的主素材与 `referenceIds`；输出：按人物顺序合并主素材和更多参考图、再追加场景并稳定去重，进入生成节点 `config.referenceIds`；验证：覆盖多人物、重复引用、场景引用和已删除素材的可理解处置。
  - [x] 任务 3.3.1：新建 `apps/desktop/src/shotReferences.test.mjs`。输入：有序人物、场景及当前素材 ID 集合；输出：人物主素材与更多参考图优先、场景随后、重复项仅保留首次、已删除素材被过滤的断言；验证方法：先运行 `pnpm --filter desktop exec node --test src/shotReferences.test.mjs`，确认因实现模块不存在而红灯。证据：Node 测试以 `ERR_MODULE_NOT_FOUND`、退出码 1 失败，证明生产收集器尚不存在。
  - [x] 任务 3.3.2：新建 `apps/desktop/src/shotReferences.ts`。输入：分镜人物引用、人物/场景 Profile、当前素材 ID 集合；输出：稳定有序且只含现存素材的参考图 ID；验证方法：3.3.1 定向测试全部通过。证据：定向测试 2 项通过，覆盖稳定去重、已删除素材过滤和档案缺失时保留显式引用。
  - [x] 任务 3.3.3：修改 `apps/desktop/src/App.tsx` 的分镜导入接入点。输入：纯函数输出；输出：生成节点 `config.referenceIds` 使用完整参考图集合；验证方法：desktop 类型检查与 3.3.1 定向测试通过。证据：定向测试 2 项与 `pnpm --filter desktop typecheck` 均以退出码 0 完成。
- [x] 任务 3.4：修改 `scripts/smoke.mjs` 的会话入口。输入：浏览器验收环境；输出：只有显式隔离 QA 会话/数据目录时才允许执行真实保存、上传、导入和设置写入，默认连接 `.runtime/session.json` 时硬失败；验证：无隔离标记失败且不发业务请求，隔离环境可继续执行。
- [x] 任务 3.5：修改 `scripts/performance.mjs` 的会话入口。输入：性能验收环境；输出：只有显式隔离 QA 会话/数据目录时才允许创建性能项目；验证：无隔离标记失败且不创建项目，隔离环境可运行。
- [x] 任务 3.6：为 `pnpm verify` 的真实媒体验证增加确定性门禁。输入：显式验证命令与 `FFMPEG_DIR`；输出：媒体工具缺失时验证失败而非 0 退出并跳过；验证：正确 bin 路径为 302 项通过，错误路径必须非零退出。涉及具体文件须在实施前根据最小改动方案补入本表。
- [x] 任务 4：完成类型/构建/后端回归和相应浏览器验证，记录缺失的外部验证。
- [x] 任务 5：独立上下文复审，处理反馈直至 SHIP 或记录真实外部阻塞。

### 验收标准
- [x] 主要模块均有审查记录，发现的问题有修复或明确处置依据。
- [x] 现有未提交修改保留，不上传数据、不泄露凭据、不调用付费生成、不自动提交推送。
- [x] 验证通过且独立复审决定 SHIP；否则明确列出未完成项及恢复路径。

### 风险点
存在用户已有未提交的提示词规则和参考图一致性修改，不回滚、不覆盖。真实云端质量和 Windows 安装包签名不属于本地测试保证。浏览器有真实写入的脚本必须使用隔离数据；运行中的创作服务不可在有任务时重启。

### 主要模块审查矩阵
| 模块 | 实际阅读范围 | 风险/问题 | 处置结果 |
|---|---|---|---|
| 前端应用 | `apps/desktop/src` 19 个文件及 desktop 的 package/vite/tsconfig | 启动 token 仅在会话成功后移除；项目切换存在逆序响应覆盖；Profile 多参考图未进入分镜生成输入；时间线空态和保存文案耦合为低优先级 | 前三项列入任务 3.1–3.3；低优先级项记录但不为凑改动重构 |
| 后端应用 | `services/backend/app` 14 个模块：API、图、存储、Worker、Provider、凭据、费用、导出、时间线、便携包、Comfy、工作流与分镜节点 | 未发现确定的高优先级数据丢失、凭据泄漏、缓存串用或重复付费提交；超大像素图片、远端媒体内容探测、WebSocket Host 对称校验为中低风险建议 | 保留建议，待完成高优先级修复后再评估；不无依据扩写范围 |
| 既有未提交基线 | `providers.py`、`shot_nodes.py`、`worker.py`、`test_shot_nodes.py` 与 `.codex/ralph-loop/baseline.patch` | 自然表演/双扇门规则、参考图 hash 顺序检查必须保留 | 审查确认边界合理；正确 FFmpeg 路径下纳入 302 项回归 |
| 生成工具边界 | `generate_tool` 三文件；大型 `workflow_json_new.py` 仅查 27 个模板结构/引用 | 应用路径有安全下载与动态凭据边界；遗留直调示例存在 import 时密钥、吞错和宽松下载，但正常应用未走该路径 | 不改云端模板语义；遗留入口列为中优先级维护建议 |
| 开发/浏览器脚本 | `scripts` 全部 Python、PowerShell、14 个 mjs | `smoke.mjs` 默认连接真实会话并写业务数据；`performance.mjs` 写入日常数据根；FFmpeg 误配时 verify 可带 skip 成功 | 列入任务 3.4–3.6，所有真实写入改用隔离数据 |
| 桌面与 CI | `src-tauri` 源码/配置、根与 desktop 包配置、CI；锁文件仅查存在与发布哈希 | PyInstaller/Rust stable/Chocolatey FFmpeg 版本漂移影响严格复现；桌面 QA 本身使用隔离目录 | 记录为维护风险；不在高优先级正确性修复前扩大打包改造 |

### 本轮验证证据
### 接续实施细化（依次执行）
- [x] 3.4.1：新建 `scripts/qa-session.test.mjs`；输入缺省、日常及隔离会话描述，输出拒绝/接受断言；先红灯验证。
- [x] 3.4.2：新建 `scripts/qa-session.mjs`；输入显式 CANVAS_QA=1、CANVAS_SESSION_FILE 和带 qa/dataDir/configDir 的清单；输出本机非 5173 URL；会话、数据和设置须在同一 `.runtime/qa-*` 目录，realpath 防链接绕过；验证 3.4.1。
- [x] 3.4.3：修改 `scripts/smoke.mjs` 会话入口为共享门禁；输入上述清单，输出隔离验收；默认执行应在浏览器启动前失败。
- [x] 3.5.1：修改 `scripts/performance.mjs` 会话入口为共享门禁；输入上述清单，输出隔离性能验收；默认执行应在浏览器启动前失败。
- [x] 3.6.1：新建 `scripts/verify-media.py`；输入 FFMPEG_DIR 或 PATH，输出 ffmpeg/ffprobe 可执行验证；显式错误目录即失败，不回退 PATH；错误目录非零、真实目录成功。
- [x] 3.6.2：修改 `package.json` verify 链，加入媒体工具预检及前端/脚本回归；输入 pnpm verify，输出缺失工具硬失败或完整验证。
- [x] 3.7：修改 `apps/desktop/src/App.tsx` 项目切换逻辑；输入保存/加载失败或重叠切换，输出恢复最后成功项目，切换期间工作区与快捷键不可编辑；浏览器验证失败恢复及逆序响应。
- [x] 3.8：修改 `apps/desktop/src/App.tsx` 参考图候选集合；输入混合 MIME 素材，输出只有 image/* ID 进入生成 config；浏览器验证多参考图顺序及音视频过滤。
- [x] 4.1：新建 `scripts/audit-browser.mjs`；输入隔离会话，输出项目切换失败/逆序及图片引用集成断言，不调用云端；记录结果。

隔离门禁契约：后端须以清单 dataDir/configDir 启动，禁止加载日常 .env 或云端密钥；清单属于可信本地启动配置，不能校验恶意伪造服务。以上文件为涉及文件表的补充。

- 错误指向不存在的 `.runtime/tools/ffmpeg/bin` 时，`pnpm verify` 为 `300 passed, 2 skipped`，证明当前门禁不足。
- 指向实际 `.runtime/tools/ffmpeg/ffmpeg-9.0.2-essentials_build/bin` 时，`pnpm verify` 为 `302 passed, 1 warning`，类型检查、Vite 构建和两项真实媒体验证均执行；构建仅有既存大 chunk 警告。
- 未调用真实生成、未重启 `localhost:5173`、未写日常业务数据、未提交或推送。

执行顺序补充：4.1 集成用例先于 3.7/3.8 编写并在旧构建上复现，再修复并重新构建验收。测试后端临时启动器位于本次 .runtime/qa-* 内，只创建独立 data/config，不读取 .env；输入随机端口和临时 token，输出隔离服务与清单，不输出 token。

4.1 红灯证据：旧构建在模拟保存503后项目选择值为空，恢复原项目断言失败（退出1）。后续同一用例复验。
- [x] 4.2：新建 scripts/qa.py 可复用隔离启动器；输入本地构建、随机端口，输出独立 data/config/session 清单；不加载 .env，清除服务密钥环境，验证真实浏览器可访问。
- [x] 4.3：更新 README.md 隔离验收步骤；输入两个终端的命令，输出可复现的 smoke/performance/audit-browser 操作，不再依赖临时脚本。

3.7 证据：构建通过，audit-browser 的保存失败恢复、加载失败恢复、inert、快捷键、逆序响应全部通过，执行到3.8断言才失败：实际参考图额外包含 audio，确认 MIME 缺陷。

3.8 证据：构建通过；完整 audit-browser 退出0，引用集合为 i1/i1-extra/i2/i3，audio 与 deleted 不进入生成 config。

- [x] 4.4：修改 scripts/smoke.mjs 的浏览器失败证据/拖线定位；输入实际无头鼠标操作，输出失败截图与端口命中证据，确认原因后最小修正脚本；保持真实拖线和断言不降级。首次失败在第86行：预期1条边，实际0。

4.4 证据：elementFromPoint 指向 node-placeholder 而非源端口，截图确认新增节点重叠。真实拖开目标后，全部连线/类型错误/循环依赖断言通过。分组选择改点可见header边缘，分组撤销重做通过。
- [x] 4.5：修改 scripts/smoke.mjs 的 savedState 等待；输入异步切换的项目选择值，输出非空项目ID后再读文档；已复现ZIP导入时not.toBe(old)接受空值导致 /canvases/ 404，验证等待后能继续媒体验收。

### 接续验证结果
### 独立复审返工：异步操作的项目归属
- [x] 5.1：修改 `scripts/audit-browser.mjs`，增加旧模板响应、双文件上传、云端开关和导出响应的延迟回归；输入真实页面 A→B、A→B→A 切换，输出当前项目/画布/素材/导出状态不被旧响应覆盖；旧构建先复现失败。
- [x] 5.2：修改 `apps/desktop/src/projectLoad.test.mjs`，增加门禁快照在两次切换后失效断言；输入旧快照和两次 begin，输出旧快照失效；先红灯。
- [x] 5.3：修改 `apps/desktop/src/projectLoad.ts`，暴露只读 snapshot；输入当前门禁，输出不增加序号的快照；5.2 转绿。
- [x] 5.4：修改 `apps/desktop/src/App.tsx` 的异步项目归属逻辑；操作开始固定项目 ID 与门禁快照，提交前/回写前校验；模板、上传、项目设置、导出提交/轮询不得跨切换回写，批量上传始终归属最初项目，切换后停止剩余上传；A→B→A 同样拒绝旧响应；检查相同回写点并最小防护。以 5.1 浏览器集成验证。
- [x] 5.5：运行最终 `pnpm verify` 和对应隔离浏览器回归，记录真实结果、保留 QA 数据并关停本次服务，更新 work-summary；独立复审结论仍由复审代理给出。

- pnpm verify：302 passed，无skip；5前端单测、1隔离门禁测试通过；类型/构建通过。保留既有Vite大chunk和Starlette弃用警告。
- 错误 FFMPEG_DIR 的 pnpm verify 退出1，真实 ffmpeg-9.0.2-essentials_build/bin 预检成功。
- audit-browser：独立App真实集成全部通过，未调用云端。
- smoke：完整画布/分组/ZIP模板/真实合成预览/服务配置/移动宽度验收PASS，无pageerror。
- performance：200节点/300连线，热启动243ms，平均59.21FPS，P95 16.7ms，无页面错误；仅代表本机无头Chromium。
- Node22.23.3、Node24.21.0分别实跑5前端单测全部通过；本机默认Node23.11.0。未声称远程CI通过。
- 本次QA目录：.runtime/qa-38da432e573847d486e22b79606c7eb9，保留数据、配置及verify/smoke日志；共享.runtime/qa中的截图/媒体/性能报告复制到本次artifacts。
- 额外参考图按角色/场景顺序稳定追加；删除项不占输出槽。收集器没有按图号给角色重新编号的逻辑，提示词锚点仍按角色姓名，无法由本地测试保证真实云端角色匹配。
- 独立复审任务保持未勾选，交协调代理执行。

5.1 红灯：旧构建中延迟 A 模板响应在切到 B 后清空 B 画布，节点预期1实际0，audit-browser 退出1。QA目录 .runtime/qa-5bf07d0d892c43f8a964a3bc14ddd2bc。

5.2 红灯：gate.snapshot is not a function；原逆序加载测试通过。

5.3 绿灯：门禁2项单测通过，快照不推进世代且两次切换后失效。

- [x] 5.6：修改 `scripts/audit-browser.mjs`，输入设置弹窗保存/恢复响应挂起、关闭弹窗后 A→B 或 A→B→A，断言旧响应不能改变当前项目及预算；先在当前构建复现。
- [x] 5.7：修改 `apps/desktop/src/App.tsx` 的 Settings.changeProject 回调，输入渲染时固定的项目作用域，输出仅相同世代可回写；5.6 转绿并通过类型构建。

- [x] 5.4.1：修正 `scripts/audit-browser.mjs` 的受控开关测试操作；输入挂起的设置响应，使用 click 发起请求，输出等待实际请求后切换项目；不要求挂起期间 checked 已成功，后续仍断言旧响应不能改变当前开关。

5.4 验证：隔离 QA .runtime/qa-dbf0082109d54d47a043e7d80f5d79fa 上 audit-browser 退出0；模板、双文件上传、云端设置、导出提交和轮询均覆盖 A→B 及 A→B→A 迟到响应。模板跨项目覆盖红灯已转绿。

5.5 最终验证：pnpm verify 退出0，302项后端、6项前端、1项隔离门禁通过，无skip；类型、构建和git diff --check通过。隔离audit-browser退出0。测试服务已关停，日常服务未重启。

5.6 红灯：设置弹窗保存请求挂起后切B，释放响应将选择器改回A，audit-browser第141行失败。

5.7 绿灯：完整audit-browser退出0，设置弹窗保存/恢复覆盖A→B和A→B→A，选择器及预算未被旧响应覆盖。

最终复验（设置弹窗修复后）：pnpm verify 退出0，构建 index-D9flITuR.js，302 passed/1既有warning/32.10s，6前端+1QA测试无skip；最新audit-browser退出0，含设置save/restore两类迟到响应。QA .runtime/qa-23bc195c0a474410ae75fb906f49ccfe；工具会话41307/62439保存执行结果。

### 最终独立复审
结论 SHIP。fresh-context final_review 实际检查最终源码和测试，确认两轮发现的模板跨项目覆盖及Settings迟到回写已修复，四个既有后端改动与baseline一致。外部Ralph CLI因容量/网络错误中断，后续以会话内独立工作→复审→返工→复审完成；不把CLI的停止状态伪称自动完成。最终无未处理高优先级阻塞。临时QA服务已关停；未调用付费生成、未重启日常服务、未提交推送。
