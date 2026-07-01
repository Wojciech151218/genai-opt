"""Smoke tests for the genai-opt package."""

import genai_opt


def test_version_is_defined() -> None:
    assert genai_opt.__version__ == "0.1.0"
