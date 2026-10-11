"""桌面 sidecar 入口，也用于 PyInstaller；启动握手仅写本地临时文件。"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import sys

if not getattr(sys, "frozen", False):
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root), str(root / "services/backend")]
else:
    root = Path(sys._MEIPASS)
    sys.path[:0] = [str(root), str(root / "services/backend")]

from dotenv import load_dotenv
import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handshake", required=True)
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    load_dotenv(Path.cwd() / ".env")
    os.environ["CANVAS_DATA_DIR"] = args.data_dir
    os.environ["CANVAS_SESSION_TOKEN"] = secrets.token_urlsafe(32)
    # 预绑定并把同一 socket 交给 uvicorn，避免随机端口检查后被占用。
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    from app.main import create_app
    app = create_app(args.data_dir, os.environ["CANVAS_SESSION_TOKEN"])
    original = app.router.lifespan_context
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def ready_lifespan(app):
        async with original(app):
            Path(args.handshake).write_text(json.dumps({"url": f"http://127.0.0.1:{port}/#token={os.environ['CANVAS_SESSION_TOKEN']}"}), encoding="utf-8")
            yield
    app.router.lifespan_context = ready_lifespan
    uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")).run(sockets=[sock])


if __name__ == "__main__":
    main()
