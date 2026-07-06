"""Tests for random_mutation."""

from genai_opt.optimizer_engine.mutation_policy.mutation_policy import random_mutation
from genai_opt.experiments.float_genome import FloatGenome


def test_random_mutation_always_true():
    """random_mutation(1.0) should always return True."""
    should_mutate = random_mutation(1.0)
    genome = FloatGenome(25.0, target=50.0)
    results = [should_mutate(genome) for _ in range(100)]
    assert all(results)


def test_random_mutation_never():
    """random_mutation(0.0) should always return False."""
    should_mutate = random_mutation(0.0)
    genome = FloatGenome(25.0, target=50.0)
    results = [should_mutate(genome) for _ in range(100)]
    assert not any(results)
