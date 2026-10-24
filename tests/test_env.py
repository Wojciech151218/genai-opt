import os
from pathlib import Path

import pytest

from genai_opt.env import find_project_root, load_openai_api_key, load_project_env


def test_find_project_root_from_repo() -> None:
    root = find_project_root(Path(__file__).resolve())
    assert (root / "pyproject.toml").exists()


def test_load_project_env_reads_dotenv(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key-from-dotenv\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("genai_opt.env.find_project_root", lambda start=None: tmp_path)

    load_project_env()

    assert os.getenv("OPENAI_API_KEY") == "test-key-from-dotenv"


def test_load_openai_api_key_prefers_explicit_value(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    assert load_openai_api_key(api_key="explicit") == "explicit"


def test_load_openai_api_key_reads_dotenv(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key-from-dotenv\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("genai_opt.env.find_project_root", lambda start=None: tmp_path)

    assert load_openai_api_key() == "test-key-from-dotenv"


def test_load_openai_api_key_raises_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("genai_opt.env.find_project_root", lambda start=None: tmp_path)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        load_openai_api_key()
