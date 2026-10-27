$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$mediaSource = $env:FFMPEG_DIR
if (-not $mediaSource) { throw '请设置 FFMPEG_DIR 为包含 ffmpeg.exe、ffprobe.exe 的发行版 bin 目录' }
$mediaPackage = Split-Path -Parent $mediaSource
$mediaDir = Join-Path $repoRoot 'apps/desktop/src-tauri/binaries/media'
foreach ($file in @('ffmpeg.exe', 'ffprobe.exe')) {
    if (-not (Test-Path -LiteralPath (Join-Path $mediaSource $file))) { throw "媒体工具缺失：$file" }
}
foreach ($file in @('LICENSE', 'README.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $mediaPackage $file))) { throw "FFmpeg 发行说明缺失：$file" }
}
New-Item -ItemType Directory -Force -Path $mediaDir | Out-Null
foreach ($file in @('ffmpeg.exe', 'ffprobe.exe')) { Copy-Item -LiteralPath (Join-Path $mediaSource $file) -Destination (Join-Path $mediaDir $file) }
foreach ($file in @('LICENSE', 'README.txt')) { Copy-Item -LiteralPath (Join-Path $mediaPackage $file) -Destination (Join-Path $mediaDir $file) }
pnpm build
if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }
$targetTriple = 'x86_64-pc-windows-msvc'
if (Get-Command rustc -ErrorAction SilentlyContinue) {
    $targetTriple = (rustc -vV | Select-String '^host: ').ToString().Substring(6)
}
$frontendData = (Join-Path $repoRoot 'apps/desktop/dist') + ';apps/desktop/dist'
$videoPromptGuideData = (Join-Path $repoRoot 'ref-en.txt') + ';.'
uv run --project services/backend --with pyinstaller pyinstaller --noconfirm --onefile --name canvas-backend --distpath .runtime/sidecar --workpath .runtime/pyinstaller --specpath .runtime --paths $repoRoot --paths (Join-Path $repoRoot 'services/backend') --collect-submodules app --collect-submodules generate_tool --collect-all uvicorn --add-data $frontendData --add-data $videoPromptGuideData scripts/backend_entry.py
if ($LASTEXITCODE -ne 0) { throw '后端打包失败' }
$binaryDir = Join-Path $repoRoot 'apps/desktop/src-tauri/binaries'
New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null
Copy-Item -LiteralPath '.runtime/sidecar/canvas-backend.exe' -Destination (Join-Path $binaryDir "canvas-backend-$targetTriple.exe")
Write-Host 'Sidecar 已生成。接下来运行 pnpm --filter desktop tauri build。'
