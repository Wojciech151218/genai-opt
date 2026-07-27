import os
from pathlib import Path

from genai_opt.env import find_project_root, load_project_env


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
