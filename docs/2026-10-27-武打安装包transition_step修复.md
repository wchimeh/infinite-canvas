## 开发文档：transition_step 可配置修复 Windows EXE 安装包

### 背景
武打节点 transition_step 可配置化及 steps 默认值恢复 10 的修复完成后，重新打包交付 Windows 安装包。

### 目标
- [x] 生成包含本次修复的 Windows x64 EXE 安装包，输出到 `dist/releases/2026-10-27-combat-steps/`。
- [x] 验证安装运行并生成校验和。

### 涉及文件
| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `docs/2026-10-27-武打安装包transition_step修复.md` | 新建 | 打包验收记录 |
| `dist/releases/2026-10-27-combat-steps/` | 新建产物 | 安装包、发布清单、校验和 |

### 任务清单（必须全部标记完成）
- [x] 任务 1：准备 FFmpeg；输入 `apps/desktop/src-tauri/binaries/media` 中的既有发行文件，输出 `.runtime/ffmpeg-dist/` 供 FFMPEG_DIR 使用。
- [x] 任务 2：验证当前源码；输入源码和 FFmpeg，输出 pnpm verify 结果。
- [x] 任务 3：打包后端；输入前后端源码，输出包含武打工作流新参数的 sidecar EXE。
- [x] 任务 4：打包桌面；输入 sidecar 和项目本地 Rust 工具链（`.runtime/cargo` + `.runtime/rustup`），输出 NSIS EXE。
- [x] 任务 5：隔离验收；输入安装包，输出安装、启动、保存重开和卸载检查结果。
- [x] 任务 6：生成发布清单；输入已验收 EXE，输出大小、SHA256 和发布记录。

### 验收标准
- [x] 源码验证、后端及桌面构建通过。
- [x] 隔离桌面验收通过。
- [x] 安装包与发布清单校验和一致。

### 风险点
版本保持 0.1.0，通过独立目录与上一版 `2026-10-27-combat` 区分；未配置数字签名。使用隔离目录验收，不调用收费生成服务。

### 验证记录
- pnpm verify 通过：1446 项后端测试全绿（含武打节点 172 项），媒体校验、语法、类型检查、前端构建与 QA 防护测试通过。
- PyInstaller 与 Tauri NSIS 构建成功；Rust 使用项目本地工具链 `.runtime/cargo`（cargo 1.99.0）。
- 隔离验收通过：独立安装、真实 WebView2、保存重开、窗口关闭后进程树退出、卸载。
- 安装包：`dist/releases/2026-10-27-combat-steps/无限画布_0.1.0_x64-setup.exe`。
- 大小：85530917 字节；SHA256：`3fb51be7428766cd3e199a9a292873c15b1d8b9e28fd33a2d7fd170fb2099f61`；manifest.json 与 SHA256SUMS 校验一致。
- 签名状态 NotSigned；未进行真实云端生成或干净 Windows 机器验证，未提交代码。
