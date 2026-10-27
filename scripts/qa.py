"""启动独立 QA 后端；不加载日常 .env、数据、设置或凭据。"""
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import uuid


def main():
    repo = Path(__file__).resolve().parents[1]
    if not (repo / 'apps/desktop/dist/index.html').is_file():
        raise SystemExit('请先运行 pnpm build')
    task = repo / '.runtime' / ('qa-' + uuid.uuid4().hex)
    for folder in ('data', 'config'):
        (task / folder).mkdir(parents=True)
    for key in ('RUNNINGHUB_API_KEY', 'TEXT_API_KEY'):
        os.environ.pop(key, None)
    os.environ['CANVAS_DATA_DIR'] = str(task / 'data')
    os.environ['CANVAS_CONFIG_DIR'] = str(task / 'config')
    os.environ['CANVAS_SESSION_TOKEN'] = secrets.token_urlsafe(32)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    session = task / 'session.json'
    session.write_text(json.dumps(dict(qa=True, dataDir=str(task / 'data'), configDir=str(task / 'config'),
                                      url=f'http://127.0.0.1:{port}/#token={os.environ["CANVAS_SESSION_TOKEN"]}')), encoding='utf-8')
    print(f'独立 QA 会话文件：{session}\n保留此终端运行；按 Ctrl+C 停止。请勿分享会话文件。', flush=True)
    sys.path[:0] = [str(repo), str(repo / 'services/backend')]
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=port, log_level='warning')


if __name__ == '__main__':
    main()
