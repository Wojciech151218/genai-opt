"""Building the generation zero population from a set of seeds."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T

S = TypeVar("S")


def cycle_seeds_initial_population_strategy(
    seeds: Sequence[S],
    create_genome: Callable[[S], T.Genome],
    *,
    population_size: int,
) -> T.InitialPopulationStrategy:
    """Return a strategy that fills a population by cycling through ``seeds``.

    When there are more slots than seeds the seeds repeat, so a handful of
    hand-written starting points can fill a larger population. Validation
    happens now rather than when the strategy is finally called, so a
    misconfigured experiment fails while it is being built.

    Args:
        seeds: Starting points, used in order and repeated as needed.
        create_genome: Builds a genome from one seed.
        population_size: How many genomes the population should hold.

    Returns:
        A zero-argument strategy suitable for
        :class:`~genai_opt.optimizer_engine.experiment_builder.ExperimentBuilder`.

    Raises:
        ValueError: If ``seeds`` is empty or ``population_size`` is not positive.
    """
    if not seeds:
        raise ValueError("seeds must not be empty")
    if population_size <= 0:
        raise ValueError("population_size must be positive")

    def create_population() -> T.Population:
        population: T.Population = Population()
        for index in range(population_size):
            population.add_genome(create_genome(seeds[index % len(seeds)]))
        return population

    return create_population


def cycle_seeds_initial_population(
    seeds: Sequence[S],
    create_genome: Callable[[S], T.Genome],
    *,
    population_size: int,
) -> T.Population:
    """Build a population immediately by cycling through ``seeds``.

    The eager counterpart of
    :func:`cycle_seeds_initial_population_strategy`, for when you want the
    population itself rather than a strategy to hand to a builder.

    Args:
        seeds: Starting points, used in order and repeated as needed.
        create_genome: Builds a genome from one seed.
        population_size: How many genomes the population should hold.

    Returns:
        The populated generation zero.

    Raises:
        ValueError: If ``seeds`` is empty or ``population_size`` is not positive.
    """
    return cycle_seeds_initial_population_strategy(
        seeds,
        create_genome,
        population_size=population_size,
    )()
