#!/usr/bin/env python3
"""
AI Code Builder — cross-platform service management script.

Works on Windows, macOS, and Linux without external dependencies.

Usage (run from the project root, or let the shell wrappers handle the cwd):
  python scripts/manage.py start   [--env ENV] [--port PORT] [--frontend] [--foreground]
  python scripts/manage.py stop    [--frontend] [--force]
  python scripts/manage.py health  [--port PORT] [--url URL]
  python scripts/manage.py status

Examples:
  python scripts/manage.py start --env development
  python scripts/manage.py start --env production --port 8080
  python scripts/manage.py stop  --frontend
  python scripts/manage.py health
  python scripts/manage.py status
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Project layout ─────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
PIDS_DIR    = ROOT / ".pids"

BACKEND_PID_FILE  = PIDS_DIR / "backend.pid"
FRONTEND_PID_FILE = PIDS_DIR / "frontend.pid"

IS_WINDOWS = platform.system() == "Windows"

# Force UTF-8 output on Windows so box-drawing / tick / cross characters
# (━  ✔  ✖  →) don't cause UnicodeEncodeError on cp1252 consoles.
if IS_WINDOWS and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Terminal colours ───────────────────────────────────────────────────────────
# Enabled on any TTY; on Windows only when running inside Windows Terminal or
# ConEmu (which set WT_SESSION / ANSICON).
_USE_COLOR = sys.stdout.isatty() and (
    not IS_WINDOWS
    or bool(os.environ.get("WT_SESSION") or os.environ.get("ANSICON"))
)


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _header(msg: str) -> None:
    print(f"\n{_c('1;35', '━━ ' + msg + ' ━━')}")


def _info(msg: str) -> None:
    print(f"  {_c('36', '→')} {msg}")


def _ok(msg: str) -> None:
    print(f"  {_c('32', '✔')} {msg}")


def _warn(msg: str) -> None:
    print(f"  {_c('33', '!')} {msg}")


def _err(msg: str) -> None:
    print(f"  {_c('31', '✖')} {msg}", file=sys.stderr)


# ── Python / venv detection ────────────────────────────────────────────────────

def _venv_python() -> Path:
    """Return the Python interpreter inside .venv, falling back to sys.executable."""
    venv = ROOT / ".venv"
    candidates = (
        [venv / "Scripts" / "python.exe"]
        if IS_WINDOWS
        else [venv / "bin" / "python3", venv / "bin" / "python"]
    )
    for p in candidates:
        if p.exists():
            return p
    return Path(sys.executable)


def _venv_pip() -> Path:
    """Return the pip executable inside .venv, falling back to system pip."""
    venv = ROOT / ".venv"
    candidates = (
        [venv / "Scripts" / "pip.exe"]
        if IS_WINDOWS
        else [venv / "bin" / "pip3", venv / "bin" / "pip"]
    )
    for p in candidates:
        if p.exists():
            return p
    fallback = shutil.which("pip3") or shutil.which("pip") or "pip"
    return Path(fallback)


# ── Dependency installation ────────────────────────────────────────────────────

def _ensure_venv() -> None:
    """Create a virtual environment at ROOT/.venv if one does not already exist."""
    venv = ROOT / ".venv"
    if venv.exists():
        return
    _info("Virtual environment not found — creating .venv …")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError("Failed to create virtual environment. Check that 'python -m venv' works.")
    _ok("Virtual environment created at .venv")


def _ensure_backend_deps() -> None:
    """Ensure .venv exists and all Python dependencies are installed."""
    req_file = BACKEND_DIR / "requirements.txt"
    if not req_file.exists():
        _warn("backend/requirements.txt not found — skipping Python dependency install.")
        return

    _ensure_venv()
    pip = _venv_pip()
    _info(f"Installing Python dependencies  (pip install -r requirements.txt) …")
    result = subprocess.run(
        [str(pip), "install", "-r", str(req_file), "-q", "--disable-pip-version-check"],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(
            "pip install failed. Check requirements.txt and your network connection."
        )
    _ok("Python dependencies up to date.")


def _ensure_frontend_deps() -> None:
    """Run 'npm install' in the frontend directory if package.json is present."""
    pkg_json = FRONTEND_DIR / "package.json"
    if not pkg_json.exists():
        _warn("frontend/package.json not found — skipping npm install.")
        return

    npm = shutil.which("npm") or "npm"
    _info("Installing frontend dependencies  (npm install) …")
    result = subprocess.run(
        [npm, "install"],
        cwd=str(FRONTEND_DIR),
    )
    if result.returncode != 0:
        raise RuntimeError(
            "npm install failed. Check frontend/package.json and your network connection."
        )
    _ok("Frontend dependencies up to date.")


# ── PID file helpers ───────────────────────────────────────────────────────────

def _write_pid(pid_file: Path, pid: int) -> None:
    PIDS_DIR.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid), encoding="utf-8")


def _read_pid(pid_file: Path) -> int | None:
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _process_running(pid: int) -> bool:
    """Return True if a process with *pid* is alive."""
    if IS_WINDOWS:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True,
        )
        return str(pid) in result.stdout
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _terminate(pid: int, *, force: bool = False) -> bool:
    """Send SIGTERM (or SIGKILL / /F on Windows) to *pid*. Returns True if signal was sent."""
    if IS_WINDOWS:
        cmd = ["taskkill", "/F", "/PID", str(pid)] if force else ["taskkill", "/PID", str(pid)]
        return subprocess.run(cmd, capture_output=True).returncode == 0
    else:
        import signal as _sig
        sig = _sig.SIGKILL if force else _sig.SIGTERM
        try:
            os.kill(pid, sig)
            return True
        except ProcessLookupError:
            return False


# ── Log directory resolution ───────────────────────────────────────────────────

def _log_dir(app_env: str) -> Path:
    """
    Resolve the log directory.
    Priority: LOG_DIR env-var → backend/.env LOG_DIR entry → OS temp fallback.
    """
    # 1. OS environment variable (set by the caller or export in the shell)
    from_env = os.environ.get("LOG_DIR", "").strip()
    if from_env:
        return Path(from_env)

    # 2. Parse LOG_DIR from backend/.env (simple key=value scan, no Python deps)
    env_file = BACKEND_DIR / ".env"
    if env_file.exists():
        raw_bytes = env_file.read_bytes()
        for enc in ("utf-8-sig", "utf-16", "latin-1"):
            try:
                text = raw_bytes.decode(enc)
                break
            except (UnicodeDecodeError, ValueError):
                continue
        else:
            text = ""
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("LOG_DIR=") and not line.startswith("#"):
                val = line.split("=", 1)[1].strip().split("#")[0].strip()
                if val:
                    return Path(val)

    # 3. Default — same logic as settings.py default_factory
    return Path(tempfile.gettempdir()) / "code_builder_logs"


# ── Uvicorn command builder ────────────────────────────────────────────────────

def _uvicorn_cmd(python: Path, port: int, app_env: str) -> list[str]:
    """Return the uvicorn argv list appropriate for *app_env*."""
    base = [str(python), "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0", "--port", str(port)]
    if app_env == "development":
        return base + ["--reload", "--log-level", "debug"]
    if app_env == "staging":
        return base + ["--workers", "2", "--log-level", "info", "--access-log"]
    # production
    return base + ["--workers", "4", "--log-level", "warning", "--access-log"]


# ── start ──────────────────────────────────────────────────────────────────────

def cmd_start(args: argparse.Namespace) -> int:
    app_env  = args.env
    port     = args.port
    fg       = args.foreground

    _header(f"Start  [{app_env.upper()}]")

    # ── Install / sync dependencies ───────────────────────────────────────────
    if args.skip_deps:
        _info("Skipping dependency installation (--skip-deps).")
    else:
        try:
            _ensure_backend_deps()
            if not args.backend_only:
                _ensure_frontend_deps()
        except RuntimeError as exc:
            _err(str(exc))
            return 3

    # ── Guard: already running? ───────────────────────────────────────────────
    pid = _read_pid(BACKEND_PID_FILE)
    if pid and _process_running(pid):
        _warn(f"Backend is already running (PID {pid}). Run 'stop' first.")
        return 1

    python = _venv_python()
    _info(f"Python  : {python}")
    _info(f"Root    : {ROOT}")

    uvicorn = _uvicorn_cmd(python, port, app_env)
    env     = {**os.environ, "APP_ENV": app_env}

    workers = 1 if app_env == "development" else (2 if app_env == "staging" else 4)
    _info(f"Command : {' '.join(uvicorn[:6])} … (workers={'--reload' if app_env == 'development' else workers})")

    # ── Foreground mode ───────────────────────────────────────────────────────
    if fg:
        _info("Running in foreground — press Ctrl+C to stop.")
        try:
            proc = subprocess.Popen(uvicorn, cwd=str(BACKEND_DIR), env=env)
            _write_pid(BACKEND_PID_FILE, proc.pid)
            proc.wait()
        except KeyboardInterrupt:
            _warn("Interrupted.")
        finally:
            BACKEND_PID_FILE.unlink(missing_ok=True)
        return 0

    # ── Background mode: redirect stdout/stderr to log file ───────────────────
    log_path = _log_dir(app_env)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"app.{app_env}.log"
    _info(f"Log file: {log_file}")

    with open(log_file, "ab") as lf:
        if IS_WINDOWS:
            proc = subprocess.Popen(
                uvicorn,
                cwd=str(BACKEND_DIR),
                env=env,
                stdout=lf,
                stderr=lf,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                    | subprocess.DETACHED_PROCESS        # type: ignore[attr-defined]
                ),
                close_fds=True,
            )
        else:
            proc = subprocess.Popen(
                uvicorn,
                cwd=str(BACKEND_DIR),
                env=env,
                stdout=lf,
                stderr=lf,
                start_new_session=True,   # detach from parent's process group
                close_fds=True,
            )

    _write_pid(BACKEND_PID_FILE, proc.pid)
    _info(f"Backend spawned (PID {proc.pid}). Waiting for health check…")

    health_url = f"http://localhost:{port}/health"
    for attempt in range(20):
        time.sleep(1)
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    _ok(f"Backend is up → {health_url}  (PID {proc.pid})")
                    _ok(f"Logs → {log_file}")
                    break
        except (urllib.error.URLError, OSError):
            print(f"    [{attempt + 1:02d}/20] Waiting…", end="\r", flush=True)
    else:
        print()
        _err("Backend did not respond to health checks. Check the log file:")
        _err(f"  {log_file}")
        return 2

    # ── Optionally start frontend dev server ──────────────────────────────────
    if not args.backend_only:
        _start_frontend(app_env, skip_deps=True)  # already installed above

    return 0


def _start_frontend(app_env: str, *, skip_deps: bool = False) -> None:
    _info("Starting frontend dev server…")
    pid = _read_pid(FRONTEND_PID_FILE)
    if pid and _process_running(pid):
        _warn(f"Frontend is already running (PID {pid}).")
        return

    if not skip_deps:
        try:
            _ensure_frontend_deps()
        except RuntimeError as exc:
            _err(str(exc))
            return

    npm = shutil.which("npm") or "npm"
    cmd = [npm, "run", "dev"]

    log_path = _log_dir(app_env)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"frontend.{app_env}.log"

    with open(log_file, "ab") as lf:
        kwargs: dict = dict(cwd=str(FRONTEND_DIR), stdout=lf, stderr=lf, close_fds=True)
        if IS_WINDOWS:
            proc = subprocess.Popen(
                cmd,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                    | subprocess.DETACHED_PROCESS        # type: ignore[attr-defined]
                ),
                **kwargs,
            )
        else:
            proc = subprocess.Popen(cmd, start_new_session=True, **kwargs)

    _write_pid(FRONTEND_PID_FILE, proc.pid)
    _ok(f"Frontend started (PID {proc.pid}) → {log_file}")


# ── stop ───────────────────────────────────────────────────────────────────────

def cmd_stop(args: argparse.Namespace) -> int:
    _header("Stop")

    targets = [("Backend", BACKEND_PID_FILE)]
    if not args.backend_only:
        targets.append(("Frontend", FRONTEND_PID_FILE))

    stopped_any = False
    for name, pid_file in targets:
        pid = _read_pid(pid_file)
        if pid is None:
            _info(f"{name}: no PID file found — not running.")
            continue
        if not _process_running(pid):
            _warn(f"{name}: PID {pid} is stale (process gone). Cleaning up.")
            pid_file.unlink(missing_ok=True)
            continue

        _info(f"Stopping {name} (PID {pid})…")
        _terminate(pid, force=args.force)

        # Wait up to 10 s for graceful exit, then force-kill
        for _ in range(10):
            time.sleep(1)
            if not _process_running(pid):
                break
        else:
            if not args.force:
                _warn(f"{name} did not exit gracefully — force killing…")
                _terminate(pid, force=True)
                time.sleep(1)

        if not _process_running(pid):
            pid_file.unlink(missing_ok=True)
            _ok(f"{name} stopped.")
            stopped_any = True
        else:
            _err(f"Could not stop {name} (PID {pid}). Try --force.")

    if not stopped_any:
        _info("No services were running.")
    return 0


# ── health ─────────────────────────────────────────────────────────────────────

def cmd_health(args: argparse.Namespace) -> int:
    _header("Health Check")
    url = args.url or f"http://localhost:{args.port}/health"
    _info(f"GET {url}")

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = json.loads(resp.read())
            _ok(f"status  : {body.get('status', '?').upper()}")
            _ok(f"env     : {body.get('env', '?')}")
            _ok(f"version : {body.get('version', '?')}")
            _ok(f"inbound : {body.get('inbound_dir', '?')}")
            _ok(f"temp    : {body.get('temp_dir', '?')}")
            _ok(f"logs    : {body.get('log_dir', '?')}")
            return 0
    except urllib.error.HTTPError as exc:
        _err(f"HTTP {exc.code}: {exc.reason}")
        return 1
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        _err(f"Could not reach {url}: {reason}")
        _warn("Is the backend running? Try:  python scripts/manage.py status")
        return 2


# ── status ─────────────────────────────────────────────────────────────────────

def cmd_status(_args: argparse.Namespace) -> int:
    _header("Service Status")
    for name, pid_file in [("Backend", BACKEND_PID_FILE), ("Frontend", FRONTEND_PID_FILE)]:
        pid = _read_pid(pid_file)
        if pid and _process_running(pid):
            _ok(f"{name:12s} running   PID {pid}")
        elif pid:
            _warn(f"{name:12s} stale PID {pid}  (process not found — run 'stop' to clean up)")
        else:
            _info(f"{name:12s} stopped")
    return 0


# ── main ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="manage.py",
        description="AI Code Builder — service management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # start
    ps = sub.add_parser("start", help="Start the backend (and optionally the frontend)")
    ps.add_argument(
        "--env",
        default=os.environ.get("APP_ENV", "development"),
        choices=["development", "staging", "production"],
        help="APP_ENV to use (default: development, or $APP_ENV)",
    )
    ps.add_argument("--port", type=int, default=8000, metavar="PORT",
                    help="Backend port (default: 8000)")
    ps.add_argument("--backend-only", action="store_true",
                    help="Start only the backend, skip the Vite frontend dev server")
    ps.add_argument("--foreground", action="store_true",
                    help="Run in foreground (blocking — useful for debugging)")
    ps.add_argument("--skip-deps", action="store_true",
                    help="Skip pip/npm dependency installation (faster restart when deps haven't changed)")

    # stop
    pp = sub.add_parser("stop", help="Stop running services (backend + frontend by default)")
    pp.add_argument("--backend-only", action="store_true",
                    help="Stop only the backend, leave the frontend running")
    pp.add_argument("--force", action="store_true",
                    help="Skip graceful shutdown and force-kill immediately")

    # health
    ph = sub.add_parser("health", help="Check the backend /health endpoint")
    ph.add_argument("--port", type=int, default=8000, metavar="PORT",
                    help="Backend port (default: 8000)")
    ph.add_argument("--url", metavar="URL",
                    help="Override the full health check URL")

    # status
    sub.add_parser("status", help="Show running/stopped status of all services")

    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()
    handlers = {
        "start":  cmd_start,
        "stop":   cmd_stop,
        "health": cmd_health,
        "status": cmd_status,
    }
    sys.exit(handlers[args.command](args) or 0)


if __name__ == "__main__":
    main()
