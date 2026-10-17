## 开发文档：Windows CI修复

### 背景
GitHub Windows validation 在安装包生成成功后，发布清单的PowerShell签名查询失败，导致产物未上传。

### 目标
- [x] 签名查询兼容Windows运行环境，失败时真实记录诊断，不阻止未签名测试安装包的清单生成。
- [x] CI使用确定的FFmpeg工具路径，兼容最新随包媒体工具要求，失败时保留报告及已生成安装包。
- [ ] 独立提交CI修复并触发GitHub验证，保留现有未提交功能改动。

### 涉及文件
| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `scripts/release.py` | 修改 | 签名查询、编码和错误证据 |
| `services/backend/tests/test_release_manifest.py` | 新建 | 签名查询失败及正常结果回归 |
| `scripts/setup-ci-media.ps1` | 新建 | 固定版本/哈希FFmpeg、输出环境路径 |
| `.github/workflows/ci.yml` | 修改 | 环境、分步验证、诊断与产物上传 |
| `docs/WindowsCI修复开发文档.md` | 新建 | 实施及远端验证记录 |

### 任务清单（必须全部标记完成）
- [x] 任务1：新增发布脚本回归测试；输入正常/未签名/异常退出/无效JSON响应，输出真实签名状态或CheckFailed且保留错误。
- [x] 任务2：修复release.py；优先pwsh，后备Windows PowerShell且移除继承的PSModulePath，固定UTF8，签名探测失败记录CheckFailed；清单不丢失。
- [x] 任务3：新增setup-ci-media.ps1；输入固定FFmpeg归档和SHA256，输出校验后的发行版及FFMPEG_DIR/GITHUB_PATH；版本或工具缺失必须失败。
- [x] 任务4：更新ci.yml；保持验证门禁，升级Action运行时、分离安装和打包步骤、设置UTF8/FFmpeg、加入发布脚本预检、保留失败诊断与已生成产物。
- [x] 任务5：本地定向测试、真实EXE清单、媒体脚本及workflow语法验证。
- [x] 任务6：准备独立分支，仅复制上述CI文件及文档；输入当前HEAD和已验证修复，输出可审查的独立差异并完成分支定向测试。
- [x] 任务7：根据远端初始化日志修正setup-uv引用；输入不存在的v10浮动标签，输出实际存在的v10.3.0版本，并核验全部Action引用。7个引用均由GitHub commits API解析到实际提交。

全部开发任务完成后提交、推送，随后在“远端验证记录”中记录GitHub Actions结果。远端验收只能发生在提交之后，不提前标记通过。

### 验收标准
- [x] 正常签名结果与未知失败明确区分，不将探测失败写为已签名或未签名。
- [ ] 安装包存在时不因清单步骤失败而丢失上传；缺失产物仍明确失败。
- [x] 固定媒体工具能被测试及打包脚本发现。
- [ ] 独立修复分支的GitHub工作流实际验证并记录结果。

### 风险点
当前工作区有大量此前功能改动，使用隔离分支只提交CI相关文件。不访问用户项目或调用收费生成；不打印凭据。日志只证实签名查询子进程失败，具体PowerShell stderr此前未输出，模块环境差异是兼容性排查方向而非已证实唯一底层原因。

### 失败证据
运行：https://github.com/wchimeh/infinite-canvas/actions/runs/38137987720 ，提交98394ce。任务114465717817的测试、sidecar和NSIS步骤均success；Generate release manifest失败，release.py第28行powershell.exe Get-AuthenticodeSignature返回1，上传被跳过。Actions Node20仅为警告，并非此次失败步骤。

### 本地验证记录
2026-10-17：当前工作区 pnpm verify 通过（363项后端、6项前端、1项QA防护测试，类型检查和构建通过）；隔离分支9项签名回归测试通过。真实安装包清单生成成功，签名为NotSigned。固定FFmpeg归档校验及执行成功，workflow YAML解析通过。隔离分支以98394ce为基线，仅包含本表5个文件；不会将尚未提交的节点功能一并发布。

### 远端验证记录
首轮运行39008808618初始化失败：astral-sh/setup-uv存在v10.3.0等完整版本，但不存在v10浮动标签。项目步骤未执行，需修正引用后重新验证。
