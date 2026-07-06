"""Unit tests for FloatGenome."""

import asyncio

import pytest

from genai_opt.experiments.float_genome import FloatGenome


def _invoke_and_evaluate(genome: FloatGenome) -> None:
    asyncio.run(genome._invoke())
    asyncio.run(genome._evaluate())


def test_genome_invocation_raises_before_invoke():
    """Accessing invocation before invoke() should raise ValueError."""
    genome = FloatGenome(phenotype=42.0)
    with pytest.raises(ValueError, match="not been invoked"):
        _ = genome.invocation


def test_genome_evaluation_raises_before_evaluate():
    """Accessing evaluation before evaluate() should raise ValueError."""
    genome = FloatGenome(phenotype=42.0)
    with pytest.raises(ValueError, match="not been evaluated"):
        _ = genome.evaluation


def test_genome_reset_evaluation():
    """After invoke+evaluate then reset_evaluation(), evaluation should raise again."""
    genome = FloatGenome(phenotype=42.0)
    _invoke_and_evaluate(genome)
    genome.reset_evaluation()
    with pytest.raises(ValueError, match="not been evaluated"):
        _ = genome.evaluation


def test_float_genome_evaluate_calculates_fitness():
    """Fitness = 100.0 - abs(invocation - target)."""
    genome = FloatGenome(phenotype=45.0, target=50.0)
    _invoke_and_evaluate(genome)
    assert genome.evaluation == pytest.approx(95.0)


def test_float_genome_mutate_returns_new_genome():
    """mutate() returns a new FloatGenome instance."""
    genome = FloatGenome(phenotype=50.0)
    mutated = asyncio.run(genome.mutate())
    assert mutated is not genome
    assert isinstance(mutated, FloatGenome)


def test_float_genome_crossover_averages():
    """Crossover of 40.0 and 60.0 should produce child with phenotype 50.0."""
    parent_a = FloatGenome(phenotype=40.0, target=50.0)
    parent_b = FloatGenome(phenotype=60.0, target=50.0)
    child = asyncio.run(parent_a.crossover(parent_b))
    assert child.phenotype == pytest.approx(50.0)
