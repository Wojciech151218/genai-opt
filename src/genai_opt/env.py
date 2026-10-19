from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

OPENAI_API_KEY_ENV = "OPENAI_API_KEY"


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists():
            return path
    return current


def load_project_env() -> None:
    """Load variables from the repository root ``.env`` if present."""
    load_dotenv(find_project_root() / ".env")


def load_openai_api_key(*, api_key: str | None = None) -> str:
    """Return an OpenAI API key from ``api_key`` or the project environment."""
    if api_key:
        return api_key
    load_project_env()
    resolved = os.getenv(OPENAI_API_KEY_ENV)
    if not resolved:
        raise RuntimeError(
            f"Set {OPENAI_API_KEY_ENV} in the environment or project ``.env``, "
            "or pass api_key explicitly."
        )
    return resolved
