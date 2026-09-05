from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_DASHBOARD_URL = "http://localhost:5173"


def dashboard_root() -> Path | None:
    """Return the Vite app directory when running from a source checkout."""
    candidate = Path(__file__).resolve().parents[3] / "dashboard"
    if (candidate / "package.json").exists():
        return candidate
    return None


def start_dashboard_ui() -> subprocess.Popen[bytes] | None:
    """Launch the React dashboard with npm. Returns None if it cannot be started."""
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

    print(f"Starting dashboard at {_DASHBOARD_URL} (engine websocket ws://localhost:8765)")
    return subprocess.Popen([npm, "run", "dev"], cwd=root)


def stop_dashboard_ui(process: subprocess.Popen[bytes] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
