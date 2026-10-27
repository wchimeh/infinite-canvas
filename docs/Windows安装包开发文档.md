## 开发文档：Windows安装版EXE

### 背景
将当前全部已开发功能打包为可安装的Windows桌面程序。

### 目标
- [x] 生成Windows x64安装EXE，包含前端、Python后端与FFmpeg工具。
- [x] 独立目录验证安装、启动、保存重开和卸载，提供文件及校验值。

### 涉及文件
| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `scripts/package-sidecar.ps1` | 修改 | 收集FFmpeg二进制及分发说明 |
| `scripts/backend_entry.py` | 修改 | 安装版发现随包媒体工具 |
| `apps/desktop/src-tauri/tauri.conf.json` | 修改 | 安装媒体工具资源 |
| `README.md` | 修改 | 更新打包及运行条件 |
| `scripts/desktop-smoke.mjs` | 修改 | 验证随包媒体工具实际提取音频 |

### 任务清单（必须全部标记完成）
- [x] 任务1：打包脚本从FFMPEG_DIR收集ffmpeg/ffprobe及LICENSE、README；输出Tauri媒体资源目录，缺失时明确失败。
- [x] 任务2：后端冻结入口在未设置FFMPEG_DIR时使用安装目录media；开发环境规则保持。
- [x] 任务3：Tauri配置打包media目录，安装路径与入口匹配。
- [x] 任务4：README更新打包工具来源、安装版无需Python及随包FFmpeg说明。
- [x] 任务5：使用现有本地Rust/MSVC、PyInstaller构建最新sidecar和NSIS安装EXE；检查产物与哈希。
- [x] 任务6：独立安装、WebView2启动、保存重开、进程退出、卸载；验证安装版发现媒体工具，补充发布记录。
- [x] 任务6.1：扩展desktop-smoke.mjs，在取消FFMPEG_DIR的进程中启动，使用安装工具生成1秒视频并通过冻结后端提取音频；独立测试项目，不改原验收项目。

### 验收标准
- [x] 安装EXE成功生成，输出明确路径、大小和SHA256。
- [x] 测试使用独立数据/配置目录，不包含用户密钥或项目，不干扰日常服务。
- [x] 安装版可启动且随包工具可执行，应用关闭后后端退出。

### 风险点
未配置代码签名；系统可能显示未知发布者。WebView2由Tauri安装器按需安装。此轮在本机隔离验证，不等同干净机器或真实云端计费验证。包含FFmpeg原分发LICENSE及README，保留来源说明。不提交或推送代码。

### 发布与验证记录
- 输出：dist/releases/2026-10-16/InfiniteCanvas_0.1.0_x64-setup.exe，85,373,960字节（81.42 MiB），Windows x64，版本0.1.0。
- SHA256：b3277d727d263307b72f9e34e41d9b827f1eb116e71b6e375188997b5655375e；签名状态NotSigned。
- 最新前端与PyInstaller后端、Tauri release和NSIS均构建成功；FFmpeg/ffprobe及LICENSE、README已随包。
- desktop-smoke.mjs通过：独立安装、真实WebView2、项目保存重开、进程树关闭、卸载；清空FFMPEG_DIR后，冻结后端仍成功使用随包工具从真实1秒视频提取音频。报告.runtime/qa/desktop.json。
- Python/JS语法检查通过。此次打包前最近全量验证为354项后端、6项前端、1项QA隔离测试通过；打包后未重复整套云端契约测试。
- 不包含.env、项目data或日常凭据；无付费云端调用，未提交推送。
