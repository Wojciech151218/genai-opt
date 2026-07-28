"""A credential-free example experiment that evolves a float toward a target.

The quickest way to watch the engine work, and the example the tests exercise.
Run it as a module, ``python -m genai_opt.experiments.simple_experiment``, or call
:func:`run_simple_experiment`.
"""

from __future__ import annotations

from pathlib import Path
from random import uniform

from genai_opt.experiments import FloatGenome
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    FilesystemCheckpointer,
    Population,
    ReproductionPolicy,
    TerminalController,
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
    """Build a generation of genomes with values drawn uniformly from 0 to 100.

    Args:
        target: The value genomes are optimized toward.
        population_size: How many genomes to create.

    Returns:
        The starting population.
    """
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
    checkpoint_dir: str | Path | None = None,
) -> ExperimentBuilder:
    """Assemble the experiment without running it.

    Use this when you want to inspect or adjust the configuration, or to drive
    ``Engine.step()`` yourself.

    Args:
        target: The value genomes are optimized toward.
        iterations: How many iterations to run before stopping.
        mutation_rate: Probability that a given offspring is mutated.
        population_size: Genomes per generation.
        checkpoint_dir: Where to write checkpoints. ``None`` keeps nothing.

    Returns:
        The configured builder.
    """
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
        checkpointer=FilesystemCheckpointer(checkpoint_dir) if checkpoint_dir else None,
        experiment_controller=TerminalController(listen_for_pause=False),
    )


def run_simple_experiment(
    target: float = TARGET_VALUE,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    checkpoint_dir: str | Path | None = ".checkpoints/simple_experiment",
) -> Population[float, float]:
    """Run the experiment to completion and return the final population.

    Resumes from ``checkpoint_dir`` when a checkpoint is already there, so
    calling this twice with the default continues the earlier run rather than
    starting over. Pass ``checkpoint_dir=None`` for a self-contained run.

    Args:
        target: The value genomes are optimized toward.
        iterations: How many iterations to run before stopping.
        mutation_rate: Probability that a given offspring is mutated.
        population_size: Genomes per generation.
        checkpoint_dir: Where to read and write checkpoints. ``None`` disables
            them.

    Returns:
        The final population, with every genome evaluated. Pick the winner with
        ``max(population.get_genome_fitness(), key=lambda item: item[1])``.
    """
    engine = (
        build_simple_experiment(
            target=target,
            iterations=iterations,
            mutation_rate=mutation_rate,
            population_size=population_size,
            checkpoint_dir=checkpoint_dir,
        )
        .build()
        .from_checkpoint()
    )
    return engine.run()


def main() -> None:
    """Run the experiment with default settings, for ``python -m`` use."""
    run_simple_experiment()


if __name__ == "__main__":
    main()
