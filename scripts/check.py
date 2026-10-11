"""Dependency-free Python/JavaScript syntax checks; TypeScript uses tsc."""
import ast
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
files = [*ROOT.joinpath('scripts').glob('*.py'),
         *ROOT.joinpath('services/backend/app').rglob('*.py'),
         *ROOT.joinpath('services/backend/tests').rglob('*.py'),
         *ROOT.joinpath('generate_tool').rglob('*.py')]
for file in files:
    ast.parse(file.read_text(encoding='utf-8-sig'), filename=str(file))
scripts = list(ROOT.joinpath('scripts').glob('*.mjs'))
for file in scripts:
    subprocess.run(['node', '--check', str(file)], check=True)
print(f'Syntax OK: {len(files)} Python files, {len(scripts)} JavaScript scripts')
