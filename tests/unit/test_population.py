"""Unit tests for Population."""

import asyncio

import pytest

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.population import Population


def _make_population(*values: float, target: float = 50.0) -> Population:
    """Helper to create a Population from phenotype values."""
    genomes = [FloatGenome(phenotype=v, target=target) for v in values]
    return Population(genomes)


def test_population_add_and_count():
    """Adding 3 genomes should give count of 3."""
    pop = Population()
    for v in (10.0, 20.0, 30.0):
        pop.add_genome(FloatGenome(phenotype=v))
    assert pop.get_genome_count() == 3


def test_population_remove_genome():
    """Removing index 1 from 3 genomes leaves 2."""
    pop = _make_population(10.0, 20.0, 30.0)
    pop.remove_genome(1)
    assert pop.get_genome_count() == 2


def test_population_remove_invalid_index():
    """Removing an out-of-range index should raise IndexError."""
    pop = _make_population(10.0, 20.0)
    with pytest.raises(IndexError):
        pop.remove_genome(99)


def test_population_evaluate_all():
    """Evaluating population should set correct fitness values."""
    pop = _make_population(50.0, 40.0, target=50.0)
    asyncio.run(pop.evaluate_population())
    fitnesses = [g.evaluation for g in pop.population]
    assert fitnesses[0] == pytest.approx(100.0)
    assert fitnesses[1] == pytest.approx(90.0)


def test_population_merge():
    """Merging two populations should combine their genomes."""
    pop_a = _make_population(10.0, 20.0)
    pop_b = _make_population(30.0)
    merged = pop_a.merge(pop_b)
    assert merged.get_genome_count() == 3


def test_get_genome_fitness():
    """get_genome_fitness() returns (genome, fitness) tuples with correct values."""
    pop = _make_population(50.0, 40.0, target=50.0)
    asyncio.run(pop.evaluate_population())
    pairs = pop.get_genome_fitness()
    assert len(pairs) == 2
    assert pairs[0][1] == pytest.approx(100.0)
    assert pairs[1][1] == pytest.approx(90.0)
