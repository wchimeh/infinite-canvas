"""开发启动器：随机本地端口、会话 token、进程清理。只依赖标准库。"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def cleanup_session(path, current, previous, opener):
    try:
        if json.loads(path.read_text(encoding="utf-8")) != current:
            return
        if previous and previous.get("port") != current["port"]:
            try:
                port = int(previous['port'])
                with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                    if response.status == 200:
                        path.write_text(json.dumps(previous), encoding="utf-8")
                        return
            except (OSError, ValueError, KeyError):
                pass
        path.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="使用已构建前端，同源启动")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    os.chdir(ROOT)
    uv = shutil.which("uv")
    pnpm = shutil.which("pnpm.cmd" if os.name == "nt" else "pnpm")
    if not uv or (not args.serve and not pnpm):
        raise SystemExit("请先安装 uv 和 pnpm，再执行 uv sync --project services/backend 与 pnpm install")
    if args.serve and not (ROOT / "apps/desktop/dist/index.html").exists():
        raise SystemExit("请先运行 pnpm build")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", args.port))
        port = sock.getsockname()[1]
    token = secrets.token_urlsafe(32)
    env = os.environ.copy()
    env["CANVAS_SESSION_TOKEN"] = token
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + str(ROOT / "services/backend")
    env["CANVAS_API_URL"] = f"http://127.0.0.1:{port}"
    env["PYTHONUNBUFFERED"] = "1"
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    session_path = Path(os.environ.get('CANVAS_SESSION_FILE') or runtime / 'session.json').resolve()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    previous_session, current_session = None, None
    try:
        previous_session = json.loads(session_path.read_text(encoding="utf-8"))
        if not isinstance(previous_session, dict):
            previous_session = None
    except (OSError, ValueError):
        pass
    processes = []
    logs = []
    try:
        log = (runtime / "backend.log").open("w", encoding="utf-8")
        logs.append(log)
        processes.append(subprocess.Popen([uv, "run", "--project", "services/backend", "uvicorn", "app.main:app", "--app-dir", "services/backend", "--host", "127.0.0.1", "--port", str(port), "--env-file", str(ROOT / ".env") if (ROOT / ".env").exists() else str(ROOT / ".env.example")], env=env, stdout=log, stderr=log))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(150):
            if processes[0].poll() is not None:
                raise RuntimeError("后端启动失败，请查看 .runtime/backend.log")
            try:
                with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("后端启动超时，请查看 .runtime/backend.log")
        ui_port = port
        if not args.serve:
            log = (runtime / "frontend.log").open("w", encoding="utf-8")
            logs.append(log)
            processes.append(subprocess.Popen([pnpm, "--filter", "desktop", "dev"], env=env, stdout=log, stderr=log))
            ui_port = 5173
            for _ in range(100):
                if processes[-1].poll() is not None:
                    raise RuntimeError("前端启动失败，请查看 .runtime/frontend.log；确认 5173 端口空闲")
                try:
                    opener.open("http://127.0.0.1:5173", timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.2)
        url = f"http://127.0.0.1:{ui_port}/#token={token}"
        current_session = {"url": url, "port": port}
        session_path.write_text(json.dumps(current_session), encoding="utf-8")
        print(f"无限画布已启动：http://127.0.0.1:{ui_port} （按 Ctrl+C 退出）", flush=True)
        print(f"本机会话地址保存在 {session_path}；请勿分享该文件。", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
                else:
                    p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        for log in logs:
            log.close()
        if current_session is not None:
            cleanup_session(session_path, current_session, previous_session, opener)


if __name__ == "__main__":
    main()
