"""Fallback behavior of the mixed mutation strategy.

This is the mechanism that keeps a paid run alive when a provider is flaky or a
reply will not parse, so its failure handling is worth pinning down.
"""

import pytest

from fakes import FakeChatModel
from genai_opt.adapters.simple_system_prompt_genome.functions import mixed_mutate_function
from genai_opt.adapters.simple_system_prompt_genome.types import SimpleSystemPromptPhenotype
from genai_opt.optimizer_engine.operation import Operation


def _phenotype() -> SimpleSystemPromptPhenotype:
    return SimpleSystemPromptPhenotype(system_prompt="write a haiku", llm=FakeChatModel())


def test_first_working_strategy_wins() -> None:
    calls: list[str] = []

    def first(phenotype):
        calls.append("first")
        return Operation(phenotype)

    def second(phenotype):
        calls.append("second")
        return Operation(phenotype)

    mutate = mixed_mutate_function([first, second])
    mutate(_phenotype())

    assert calls == ["first"]


def test_a_failing_strategy_falls_through_to_the_next() -> None:
    def failing(phenotype):
        raise RuntimeError("provider unavailable")

    def working(phenotype):
        return Operation(phenotype)

    mutate = mixed_mutate_function([failing, working])
    operation = mutate(_phenotype())

    assert operation.value.system_prompt == "write a haiku"


def test_all_strategies_failing_raises() -> None:
    def failing(phenotype):
        raise RuntimeError("provider unavailable")

    mutate = mixed_mutate_function([failing, failing])

    with pytest.raises(ValueError, match="No mutate function succeeded"):
        mutate(_phenotype())


def test_an_empty_strategy_list_is_rejected_at_construction() -> None:
    """Misconfiguration should surface while building, not mid-run."""
    with pytest.raises(ValueError, match="must not be empty"):
        mixed_mutate_function([])
