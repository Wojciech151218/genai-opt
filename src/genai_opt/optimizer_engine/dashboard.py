from __future__ import annotations

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from genai_opt.optimizer_engine.dashboard_api import (
    DEFAULT_DASHBOARD_API_HOST,
    DEFAULT_DASHBOARD_API_PORT,
    DashboardAPIServer,
)

_DASHBOARD_URL = "http://localhost:5173"


@dataclass
class DashboardHandle:
    """Tracks the Vite frontend process and background SQLite HTTP API server."""

    ui_process: subprocess.Popen[bytes] | None
    api_server: DashboardAPIServer | None = None


def dashboard_root() -> Path | None:
    """Return the Vite app directory when running from a source checkout."""
    candidate = Path(__file__).resolve().parents[3] / "dashboard"
    if (candidate / "package.json").exists():
        return candidate
    return None


def start_dashboard_ui(
    *,
    api_host: str = DEFAULT_DASHBOARD_API_HOST,
    api_port: int = DEFAULT_DASHBOARD_API_PORT,
) -> DashboardHandle | None:
    """Launch the SQLite history API server and the React dashboard with npm."""
    root = dashboard_root()
    if root is None:
        print(
            "Dashboard sources were not found. From a source checkout run: cd dashboard && npm run dev",
            file=sys.stderr,
        )
        return None

    npm = shutil.which("npm")
    if npm is None:
        print("npm was not found on PATH; start the dashboard manually.", file=sys.stderr)
        return None

    if not (root / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=root, check=True)

    api_server = DashboardAPIServer(host=api_host, port=api_port)
    started_api = api_server.start()
    if not started_api:
        api_server = None

    print(
        f"Starting dashboard at {_DASHBOARD_URL} (engine ws://localhost:8765, db api http://{api_host}:{api_port}/api)"
    )
    ui_process = subprocess.Popen([npm, "run", "dev"], cwd=root)
    return DashboardHandle(ui_process=ui_process, api_server=api_server)


def stop_dashboard_ui(handle: DashboardHandle | subprocess.Popen[bytes] | None) -> None:
    if handle is None:
        return

    if isinstance(handle, DashboardHandle):
        if handle.api_server is not None:
            handle.api_server.stop()
        process = handle.ui_process
    else:
        process = handle

    if process is None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> None:
    """Launch the web dashboard and SQLite Database Explorer in standalone mode."""
    handle = start_dashboard_ui()
    if handle is None or handle.ui_process is None:
        sys.exit(1)

    try:
        while handle.ui_process.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    finally:
        stop_dashboard_ui(handle)


if __name__ == "__main__":
    main()
