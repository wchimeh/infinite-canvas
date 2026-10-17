param(
    [string]$ArchivePath = '',
    [string]$ToolRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '.runtime/ci-media')
)
$ErrorActionPreference = 'Stop'
$version = '9.0.2'
$expectedHash = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'
New-Item -ItemType Directory -Force -Path $ToolRoot | Out-Null
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $ToolRoot "ffmpeg-$version.zip"
    if (-not (Test-Path -LiteralPath $ArchivePath)) {
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-$version-essentials_build.zip" -OutFile $ArchivePath
    }
}
if ((Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'FFmpeg archive SHA256 does not match the pinned distribution'
}
Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ToolRoot -Force
$distribution = Join-Path $ToolRoot "ffmpeg-$version-essentials_build"
$mediaBin = Join-Path $distribution 'bin'
foreach ($relative in @('bin/ffmpeg.exe', 'bin/ffprobe.exe', 'LICENSE', 'README.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $distribution $relative))) { throw "Missing FFmpeg distribution file: $relative" }
}
$mediaBin = (Resolve-Path -LiteralPath $mediaBin).Path
foreach ($tool in @('ffmpeg.exe', 'ffprobe.exe')) {
    & (Join-Path $mediaBin $tool) -version
    if ($LASTEXITCODE -ne 0) { throw "$tool is not executable" }
}
$env:FFMPEG_DIR = $mediaBin
$env:Path = "$mediaBin;$env:Path"
if ($env:GITHUB_ENV) { "FFMPEG_DIR=$mediaBin" | Out-File -LiteralPath $env:GITHUB_ENV -Encoding utf8 -Append }
if ($env:GITHUB_PATH) { $mediaBin | Out-File -LiteralPath $env:GITHUB_PATH -Encoding utf8 -Append }
Write-Host "Verified FFmpeg $version at $mediaBin"
