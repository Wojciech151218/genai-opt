"""Unit tests for the Vite dashboard process launcher."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from genai_opt.optimizer_engine.dashboard import (
    DashboardHandle,
    dashboard_root,
    start_dashboard_ui,
    stop_dashboard_ui,
)


def test_dashboard_root_finds_checkout_dashboard() -> None:
    root = dashboard_root()
    assert root is not None
    assert (root / "package.json").exists()


def test_dashboard_root_returns_none_when_package_json_missing(tmp_path: Path) -> None:
    fake_module = tmp_path / "src" / "genai_opt" / "optimizer_engine" / "dashboard.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.write_text("# stub\n")
    # parents[3] from optimizer_engine/dashboard.py -> repo root; leave it without dashboard/
    with patch("genai_opt.optimizer_engine.dashboard.__file__", str(fake_module)):
        assert dashboard_root() is None


def test_start_dashboard_ui_returns_none_without_sources() -> None:
    with patch("genai_opt.optimizer_engine.dashboard.dashboard_root", return_value=None):
        assert start_dashboard_ui() is None


def test_start_dashboard_ui_returns_none_without_npm(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}")
    with (
        patch("genai_opt.optimizer_engine.dashboard.dashboard_root", return_value=tmp_path),
        patch("genai_opt.optimizer_engine.dashboard.shutil.which", return_value=None),
    ):
        assert start_dashboard_ui() is None


def test_start_dashboard_ui_launches_api_and_vite(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "node_modules").mkdir()
    mock_proc = MagicMock()
    mock_api = MagicMock()
    mock_api.start.return_value = True

    with (
        patch("genai_opt.optimizer_engine.dashboard.dashboard_root", return_value=tmp_path),
        patch("genai_opt.optimizer_engine.dashboard.shutil.which", return_value="/usr/bin/npm"),
        patch("genai_opt.optimizer_engine.dashboard.DashboardAPIServer", return_value=mock_api),
        patch("genai_opt.optimizer_engine.dashboard.subprocess.Popen", return_value=mock_proc) as popen,
        patch("genai_opt.optimizer_engine.dashboard.subprocess.run") as run,
    ):
        handle = start_dashboard_ui(api_host="127.0.0.1", api_port=9999)

    assert handle is not None
    assert handle.ui_process is mock_proc
    assert handle.api_server is mock_api
    run.assert_not_called()
    popen.assert_called_once()
    mock_api.start.assert_called_once()


def test_start_dashboard_ui_installs_node_modules_when_missing(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}")
    mock_proc = MagicMock()
    mock_api = MagicMock()
    mock_api.start.return_value = False

    with (
        patch("genai_opt.optimizer_engine.dashboard.dashboard_root", return_value=tmp_path),
        patch("genai_opt.optimizer_engine.dashboard.shutil.which", return_value="/usr/bin/npm"),
        patch("genai_opt.optimizer_engine.dashboard.DashboardAPIServer", return_value=mock_api),
        patch("genai_opt.optimizer_engine.dashboard.subprocess.Popen", return_value=mock_proc),
        patch("genai_opt.optimizer_engine.dashboard.subprocess.run") as run,
    ):
        handle = start_dashboard_ui()

    assert handle is not None
    assert handle.api_server is None
    run.assert_called_once()


def test_stop_dashboard_ui_noop_on_none() -> None:
    stop_dashboard_ui(None)


def test_stop_dashboard_ui_terminates_handle() -> None:
    proc = MagicMock()
    api = MagicMock()
    stop_dashboard_ui(DashboardHandle(ui_process=proc, api_server=api))
    api.stop.assert_called_once()
    proc.terminate.assert_called_once()
    proc.wait.assert_called_once_with(timeout=5)


def test_stop_dashboard_ui_kills_on_timeout() -> None:
    proc = MagicMock()
    proc.wait.side_effect = subprocess.TimeoutExpired(cmd="npm", timeout=5)
    stop_dashboard_ui(proc)
    proc.terminate.assert_called_once()
    proc.kill.assert_called_once()


def test_stop_dashboard_ui_skips_missing_process() -> None:
    stop_dashboard_ui(DashboardHandle(ui_process=None, api_server=None))
