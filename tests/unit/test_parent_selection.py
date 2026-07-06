"""Tests for parent selection algorithms."""

import asyncio

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import (
    rank_selection,
    roulette_wheel_selection,
    tournament_selection,
)


def _make_evaluated_population(phenotypes, target=50.0):
    """Helper: create a Population of evaluated FloatGenomes."""
    pop = Population()
    for p in phenotypes:
        pop.add_genome(FloatGenome(p, target=target))
    asyncio.run(pop.evaluate_population())
    return pop


def test_tournament_selection_returns_pair():
    """tournament_selection should return a tuple of 2 Genome instances."""
    pop = _make_evaluated_population([10.0, 20.0, 30.0, 40.0, 50.0])
    parent_a, parent_b = tournament_selection(pop)
    assert isinstance(parent_a, Genome)
    assert isinstance(parent_b, Genome)


def test_roulette_wheel_selection_returns_pair():
    """roulette_wheel_selection should return a tuple of 2 Genome instances."""
    # All fitness values must be positive for roulette wheel.
    # target=50, phenotypes close to 50 => fitness = 100 - |p - 50| > 0
    pop = _make_evaluated_population([45.0, 46.0, 47.0, 48.0, 49.0])
    parent_a, parent_b = roulette_wheel_selection(pop)
    assert isinstance(parent_a, Genome)
    assert isinstance(parent_b, Genome)


def test_rank_selection_returns_best():
    """rank_selection should return the genome with the best fitness twice."""
    pop = _make_evaluated_population([10.0, 50.0, 90.0], target=50.0)
    # Fitness: 100-|10-50|=60, 100-|50-50|=100, 100-|90-50|=60
    parent_a, parent_b = rank_selection(pop)
    assert parent_a.evaluation == 100.0
    assert parent_b.evaluation == 100.0
    assert parent_a.phenotype == 50.0
    assert parent_b.phenotype == 50.0
