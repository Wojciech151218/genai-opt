from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists():
            return path
    return current


def load_project_env() -> None:
    """Load variables from the repository root ``.env`` if present."""
    load_dotenv(find_project_root() / ".env")
