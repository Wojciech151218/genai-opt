from __future__ import annotations

import asyncio
from pathlib import Path
from random import uniform

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Population,
    ReproductionPolicy,
    SqliteCheckpointer,
    WebSocketExperimentController,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
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
    checkpoint_db: str | Path | None = None,
    *,
    experiment_id: str = "simple_experiment",
    websocket_host: str = "localhost",
    websocket_port: int = 8765,
) -> ExperimentBuilder:
    checkpointer = (
        SqliteCheckpointer(db_path=checkpoint_db, experiment_id=experiment_id) if checkpoint_db is not None else None
    )
    return ExperimentBuilder(
        inital_population_strategy=lambda: create_initial_population(
            target=target,
            population_size=population_size,
        ),
        convergence_criterion=iteration_limited_convergence(iterations),
        mutation_policy=random_mutation(mutation_rate),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(population_size),
            tournament_selection,
        ),
        checkpointer=checkpointer,
        experiment_controller=WebSocketExperimentController(host=websocket_host, port=websocket_port),
    )


async def run_simple_experiment(
    target: float = TARGET_VALUE,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    checkpoint_db: str | Path | None = ".checkpoints/simple_experiment.db",
    *,
    launch_ui: bool = False,
) -> Population[float, float]:
    builder = build_simple_experiment(
        target=target,
        iterations=iterations,
        mutation_rate=mutation_rate,
        population_size=population_size,
        checkpoint_db=checkpoint_db,
    )
    if launch_ui:
        builder.start_dashboard()
        
    engine = builder.build().from_checkpoint()
    return await engine.run()


def main() -> None:
    asyncio.run(run_simple_experiment(launch_ui=True))


if __name__ == "__main__":
    main()
