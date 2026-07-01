from __future__ import annotations

import asyncio
from random import uniform

from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import (
    convergence_function,
)
from genai_opt.optimizer_engine.experiment_builder import ExperimentBuilder
from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.metrics_collector.terminal_logger import (
    TerminalLoggerMetricsCollector,
)
from genai_opt.optimizer_engine.mutation_policy.mutation_policy import random_mutation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import (
    tournament_selection,
)
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import (
    ReproductionPolicy,
)
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import (
    generational_reproduction,
)

TARGET_VALUE = 50.0
DEFAULT_ITERATIONS = 10
DEFAULT_MUTATION_RATE = 0.2
DEFAULT_POPULATION_SIZE = 20


def create_initial_population(
    target: float = TARGET_VALUE,
    population_size: int = DEFAULT_POPULATION_SIZE,
) -> Population[float, float]:
    population = Population()
    for _ in range(population_size):
        value = uniform(0.0, 100.0)
        population.add_genome(FloatGenome(value, target=target))
    return population


def build_simple_experiment(
    target: float = TARGET_VALUE,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
) -> ExperimentBuilder:
    return ExperimentBuilder(
        inital_population_strategy=lambda: create_initial_population(
            target=target,
            population_size=population_size,
        ),
        convergence_criterion=convergence_function(iterations),
        mutation_policy=random_mutation(mutation_rate),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(
                population_size,
                tournament_selection,
            )
        ),
        metrics_collector=TerminalLoggerMetricsCollector(),
    )


async def run_simple_experiment(
    target: float = TARGET_VALUE,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
) -> Population[float, float]:
    engine = build_simple_experiment(
        target=target,
        iterations=iterations,
        mutation_rate=mutation_rate,
        population_size=population_size,
    ).build()
    return await engine.run()


def main() -> None:
    asyncio.run(run_simple_experiment())


if __name__ == "__main__":
    main()
