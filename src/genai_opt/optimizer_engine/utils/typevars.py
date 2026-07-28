from __future__ import annotations

from typing import TypeVar

P = TypeVar("P")
"""A genome's phenotype: the candidate representation being optimized."""

Inv = TypeVar("Inv")
"""The result of invoking a genome, before it is scored into a fitness value."""
