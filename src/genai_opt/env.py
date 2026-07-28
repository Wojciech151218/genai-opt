"""Loading credentials from the repository's ``.env`` file.

Provided so that running an experiment from a checkout picks up ``OPENAI_API_KEY``
without extra setup. Nothing here writes to ``.env``, and keys are never recorded
in checkpoints.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward looking for the directory that holds ``pyproject.toml``.

    Args:
        start: Where to begin. Defaults to the current working directory.

    Returns:
        The first ancestor containing ``pyproject.toml``, or the starting
        directory when there is none, which is the normal case for an installed
        package.
    """
    current = (start or Path.cwd()).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists():
            return path
    return current


def load_project_env() -> None:
    """Load variables from the repository root ``.env`` if present.

    Existing environment variables win, so an explicitly exported key is never
    overridden by the file. Does nothing when no ``.env`` exists.
    """
    load_dotenv(find_project_root() / ".env")
