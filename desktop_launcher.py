"""Windows launcher used by the downloadable desktop package."""

import argparse
import json
import os
import secrets
import socket
import threading
import webbrowser
from pathlib import Path


def find_available_port(start: int = 8000, attempts: int = 50) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("没有可用端口，请关闭占用 8000-8049 端口的程序后重试")


def application_data_dir() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or Path.home())
    target = root / "StudentAnalytics"
    target.mkdir(parents=True, exist_ok=True)
    return target


def configure_environment() -> None:
    data_dir = application_data_dir()
    secret_file = data_dir / "session.secret"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    os.environ.setdefault("DATABASE_PATH", str(data_dir / "students.db"))
    os.environ.setdefault("SECRET_KEY", secret_file.read_text(encoding="utf-8").strip())
    os.environ.setdefault("COOKIE_SECURE", "0")


def main() -> None:
    parser = argparse.ArgumentParser(description="学生学业数据分析平台 Windows 启动器")
    parser.add_argument("--check", action="store_true", help="只检查运行环境，不启动服务")
    args = parser.parse_args()
    port = find_available_port()
    if args.check:
        print(json.dumps({"status": "ok", "available_port": port}, ensure_ascii=False))
        return

    configure_environment()
    url = f"http://127.0.0.1:{port}/login"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    import uvicorn

    uvicorn.run("webapp.main:app", host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
