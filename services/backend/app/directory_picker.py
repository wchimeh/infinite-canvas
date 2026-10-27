"""Windows folder picker, isolated from configuration writes."""
import base64
import os
from pathlib import Path
import subprocess
import threading

_lock = threading.Lock()
_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Windows.Forms
$dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
$owner = [System.Windows.Forms.Form]::new()
try {
    $owner.TopMost = $true
    $owner.ShowInTaskbar = $false
    $dialog.Description = '选择项目数据保存文件夹（选择后仍需点击保存）'
    $dialog.ShowNewFolderButton = $true
    if ([System.IO.Directory]::Exists($env:CANVAS_PICKER_INITIAL)) {
        $dialog.SelectedPath = $env:CANVAS_PICKER_INITIAL
    }
    if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
        [Console]::Write($dialog.SelectedPath)
    }
} finally {
    $dialog.Dispose()
    $owner.Dispose()
}
"""


def executable():
    if os.name != 'nt':
        return None
    path = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    return path if path.is_file() else None


def pick_directory(initial=''):
    if not isinstance(initial, str) or '\x00' in initial or len(initial) > 32767:
        raise ValueError('当前目录格式无效，请手动输入保存路径')
    program = executable()
    if not program:
        raise ValueError('当前环境不支持文件夹选择，请手动输入完整路径')
    if not _lock.acquire(blocking=False):
        raise ValueError('文件夹选择窗口已经打开，请先完成选择或取消')
    try:
        # 用户路径仅作为环境变量传递，绝不拼入脚本。
        environment = {**os.environ, 'CANVAS_PICKER_INITIAL': initial}
        result = subprocess.run(
            [str(program), '-NoProfile', '-STA', '-NonInteractive', '-EncodedCommand',
             base64.b64encode(_SCRIPT.encode('utf-16-le')).decode('ascii')],
            env=environment, capture_output=True, encoding='utf-8', errors='replace',
            timeout=120, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return result.stdout.strip() or None
    except subprocess.TimeoutExpired as exc:
        raise ValueError('文件夹选择已超时关闭，请重新选择或手动输入路径') from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('无法打开文件夹选择窗口，请手动输入完整路径') from exc
    finally:
        _lock.release()
