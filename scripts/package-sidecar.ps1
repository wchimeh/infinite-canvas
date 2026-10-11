$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
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
