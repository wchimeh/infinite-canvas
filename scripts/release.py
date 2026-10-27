"""Generate a local release manifest; never infer external acceptance from mocks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def windows_signature(installer):
    # Avoid loading PowerShell 7 module paths into Windows PowerShell 5.1.
    env = {key: value for key, value in os.environ.items() if key.lower() != 'psmodulepath'}
    env['CANVAS_RELEASE_FILE'] = str(installer)
    shell = shutil.which('pwsh') or shutil.which('powershell.exe') or 'powershell.exe'
    command = ("$ErrorActionPreference='Stop'; "
               "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); "
               "$s=Get-AuthenticodeSignature -LiteralPath $env:CANVAS_RELEASE_FILE; "
               "$subject=$null; if ($null -ne $s.SignerCertificate) {$subject=$s.SignerCertificate.Subject}; "
               "@{status=$s.Status.ToString();subject=$subject}|ConvertTo-Json -Compress")
    try:
        result = subprocess.run([shell, '-NoProfile', '-NonInteractive', '-Command', command],
                                env=env, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', check=True, timeout=30)
        signature = json.loads(result.stdout.lstrip('\ufeff'))
        if not isinstance(signature, dict) or not isinstance(signature.get('status'), str) or not signature['status']:
            raise ValueError('Signature probe returned no status')
        return signature
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        detail = getattr(exc, 'stderr', None) or str(exc)
        if isinstance(detail, bytes):
            detail = detail.decode('utf-8', errors='replace')
        print('Warning: signature check failed: ' + detail[-2000:], file=sys.stderr)
        return {'status': 'CheckFailed', 'subject': None, 'error': detail[-2000:]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('installer', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/release')
    args = parser.parse_args()
    installer = args.installer.resolve(strict=True)
    signature = {'status': 'NotChecked', 'subject': None}
    if os.name == 'nt':
        signature = windows_signature(installer)
    locks = ['pnpm-lock.yaml', 'services/backend/uv.lock', 'apps/desktop/src-tauri/Cargo.lock']
    dependencies = {}
    for name in locks:
        source = ROOT / name
        dependencies[name] = {'sha256': digest(source)}
        if source.suffix == '.lock':
            dependencies[name]['packages'] = [
                {key: package[key] for key in ('name', 'version', 'source', 'checksum') if key in package}
                for package in tomllib.loads(source.read_text(encoding='utf-8')).get('package', [])]
    npm = subprocess.run(['cmd', '/c', 'pnpm', 'list', '-r', '--depth', 'Infinity', '--json'] if os.name == 'nt'
                         else ['pnpm', 'list', '-r', '--depth', 'Infinity', '--json'],
                         cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    dependencies['installedNodeGraph'] = json.loads(npm.stdout)
    evidence = {}
    for name in ('desktop', 'performance'):
        source = ROOT / '.runtime/qa' / (name + '.json')
        evidence[name] = {'sha256': digest(source), 'report': json.loads(source.read_text(encoding='utf-8'))} if source.exists() else None
    report = {'generatedAt': datetime.now(timezone.utc).isoformat(),
              'artifact': {'name': installer.name, 'bytes': installer.stat().st_size, 'sha256': digest(installer)},
              'signature': signature, 'dependencies': dependencies, 'evidence': evidence,
              'externalAcceptance': {'cloud': 'pending', 'comfyui': 'pending', 'cleanWindows': 'pending'},
              'commands': ['pnpm verify', 'pnpm test:browser', 'pnpm test:performance',
                           'node scripts/desktop-smoke.mjs <installer>']}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.output / 'SHA256SUMS').write_text(f"{report['artifact']['sha256']}  {installer.name}\n", encoding='utf-8')
    print(f"Release manifest: {args.output}; signature: {signature['status']}")


if __name__ == '__main__':
    main()
