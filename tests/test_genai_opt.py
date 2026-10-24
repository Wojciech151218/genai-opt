"""Smoke tests for the genai-opt package."""

import re
from importlib.metadata import version

import genai_opt


def test_version_is_a_release_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", genai_opt.__version__), genai_opt.__version__


def test_distribution_metadata_matches_the_source() -> None:
    # The distribution version is declared dynamically from __version__. Asserting
    # they agree is what stops a tag from shipping a wheel labelled differently;
    # pinning the literal string here would only restate a constant.
    assert version("genai-opt") == genai_opt.__version__
