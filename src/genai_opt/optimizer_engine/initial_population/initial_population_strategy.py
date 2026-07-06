from __future__ import annotations

from collections.abc import Callable, Sequence

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T


def cycle_seeds_initial_population_strategy[S](
    seeds: Sequence[S],
    create_genome: Callable[[S], T.Genome],
    *,
    population_size: int,
) -> T.InitialPopulationStrategy:
    if not seeds:
        raise ValueError("seeds must not be empty")
    if population_size <= 0:
        raise ValueError("population_size must be positive")

    def create_population() -> T.Population:
        population = Population()
        for index in range(population_size):
            population.add_genome(create_genome(seeds[index % len(seeds)]))
        return population

    return create_population


def cycle_seeds_initial_population[S](
    seeds: Sequence[S],
    create_genome: Callable[[S], T.Genome],
    *,
    population_size: int,
) -> T.Population:
    return cycle_seeds_initial_population_strategy(
        seeds,
        create_genome,
        population_size=population_size,
    )()
