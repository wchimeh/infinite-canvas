import subprocess

import pytest

from scripts import release


@pytest.mark.parametrize('status,subject', [('NotSigned', None), ('Valid', 'CN=测试发布者')])
def test_signature_probe_reports_status(tmp_path, monkeypatch, status, subject):
    import json
    def run(args, **kwargs):
        assert kwargs['encoding'] == 'utf-8'
        assert 'PSModulePath' not in kwargs['env']
        assert args[0] == 'pwsh.exe'
        return subprocess.CompletedProcess(args, 0, json.dumps({'status': status, 'subject': subject}), '')
    monkeypatch.setenv('PSModulePath', 'incompatible-modules')
    monkeypatch.setattr(release.shutil, 'which', lambda name: 'pwsh.exe')
    monkeypatch.setattr(release.subprocess, 'run', run)
    assert release.windows_signature(tmp_path / '中文安装包.exe') == {'status': status, 'subject': subject}


@pytest.mark.parametrize('failure', [
    subprocess.CalledProcessError(1, 'powershell', stderr='Security module unavailable'),
    OSError('shell unavailable'),
    subprocess.TimeoutExpired('powershell', 30),
])
def test_signature_probe_failure_is_explicit(tmp_path, monkeypatch, failure):
    def run(*args, **kwargs):
        raise failure
    monkeypatch.setattr(release.subprocess, 'run', run)
    result = release.windows_signature(tmp_path / 'app.exe')
    assert result['status'] == 'CheckFailed' and result['subject'] is None
    assert result['error']


@pytest.mark.parametrize('output', ['broken', 'null', '{}', '[]'])
def test_invalid_signature_json_is_not_success(tmp_path, monkeypatch, output):
    monkeypatch.setattr(release.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, output, ''))
    assert release.windows_signature(tmp_path / 'app.exe')['status'] == 'CheckFailed'
