"""Generate a local release manifest; never infer external acceptance from mocks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('installer', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/release')
    args = parser.parse_args()
    installer = args.installer.resolve(strict=True)
    signature = {'status': 'NotChecked', 'subject': None}
    if os.name == 'nt':
        env = {**os.environ, 'CANVAS_RELEASE_FILE': str(installer)}
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
            '$s=Get-AuthenticodeSignature -LiteralPath $env:CANVAS_RELEASE_FILE; '
            '@{status=$s.Status.ToString();subject=$s.SignerCertificate.Subject}|ConvertTo-Json -Compress'],
            env=env, capture_output=True, text=True, check=True)
        signature = json.loads(result.stdout)
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
