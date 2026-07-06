import pytest

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.initial_population import (
    cycle_seeds_initial_population,
    cycle_seeds_initial_population_strategy,
)


def test_cycle_seeds_initial_population_cycles_through_seeds() -> None:
    seeds = (1.0, 2.0, 3.0)
    population = cycle_seeds_initial_population(
        seeds,
        lambda value: FloatGenome(value, target=50.0),
        population_size=5,
    )

    assert population.get_genome_count() == 5
    for index, genome in enumerate(population.population):
        assert genome.phenotype == seeds[index % len(seeds)]


def test_cycle_seeds_initial_population_strategy_is_reusable() -> None:
    strategy = cycle_seeds_initial_population_strategy(
        [10.0, 20.0],
        lambda value: FloatGenome(value),
        population_size=2,
    )

    first = strategy()
    second = strategy()

    assert first.get_genome_count() == 2
    assert second.get_genome_count() == 2
    assert first.population[0].phenotype == 10.0
    assert second.population[1].phenotype == 20.0


def test_cycle_seeds_initial_population_rejects_empty_seeds() -> None:
    with pytest.raises(ValueError, match="seeds must not be empty"):
        cycle_seeds_initial_population([], lambda value: FloatGenome(value), population_size=1)


def test_cycle_seeds_initial_population_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError, match="population_size must be positive"):
        cycle_seeds_initial_population([1.0], lambda value: FloatGenome(value), population_size=0)
