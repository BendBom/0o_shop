"""
Запуск всех сервисов одной командой: python run.py
- FastAPI (API)        -> http://localhost:8000
- FastAPI Swagger docs -> http://localhost:8000/docs
- Flask (админка)      -> http://localhost:5000/admin/login
- Frontend             -> http://localhost:5500/index.html
"""

from pathlib import Path
import argparse
import os
import subprocess
import sys
import time


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
PROCESSES = []


def start_process(name, command, cwd=None):
    process = subprocess.Popen(command, cwd=cwd)
    PROCESSES.append((name, process))
    return process


def terminate_process(name, process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.terminate()


def shutdown():
    for name, process in reversed(PROCESSES):
        terminate_process(name, process)
    time.sleep(0.5)
    for _, process in PROCESSES:
        if process.poll() is None:
            process.kill()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload")
    args = parser.parse_args()

    print("=== O_Shop: Запуск серверов ===\n")
    print("  API:       http://localhost:8000")
    print("  Swagger:   http://localhost:8000/docs")
    print("  Админка:   http://localhost:5000/admin/login")
    print("  Фронтенд:  http://localhost:5500/index.html")
    print("\n  Ctrl+C чтобы остановить все сервисы\n")

    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    if args.reload:
        uvicorn_cmd.append("--reload")

    start_process("fastapi", uvicorn_cmd, cwd=BASE_DIR)
    start_process("flask", [sys.executable, "admin_app.py"], cwd=BASE_DIR)
    start_process("frontend", [sys.executable, "-m", "http.server", "5500"], cwd=FRONTEND_DIR)

    try:
        while True:
            for name, process in PROCESSES:
                if process.poll() is not None:
                    print(f"\n[{name}] завершился с кодом {process.returncode}. Останавливаю остальные.")
                    shutdown()
                    return process.returncode
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nОстанавливаю сервисы...")
        shutdown()
        print("Серверы остановлены.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
