"""Resuming a run from a checkpoint taken at each of the five phases.

The engine's claim is that an interrupted run continues without repeating the
phase it had already completed. That claim only holds if it is true at every
phase boundary, including the ones where offspring exist but have not replaced
the population yet.
"""

import asyncio

import pytest

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.checkpointer import FilesystemCheckpointer
from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import (
    iteration_limited_convergence,
)
from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.mutation_policy.mutation_policy import random_mutation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import tournament_selection
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import ReproductionPolicy
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import (
    generational_reproduction,
)

POPULATION_SIZE = 6
ITERATIONS = 3

PHASE_ORDER = [
    IterationPhase.EVALUATE_POPULATION,
    IterationPhase.REPRODUCE,
    IterationPhase.MUTATE,
    IterationPhase.EVALUATE_OFFSPRING,
    IterationPhase.REPLACE,
]


def _build_engine(checkpointer: FilesystemCheckpointer | None = None) -> Engine:
    genomes = [FloatGenome(float(value), target=50.0) for value in range(0, POPULATION_SIZE * 10, 10)]
    return Engine(
        population=Population(genomes),
        convergence_criterion=iteration_limited_convergence(ITERATIONS),
        mutation_policy=random_mutation(0.5),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(POPULATION_SIZE),
            tournament_selection,
        ),
        checkpointer=checkpointer,
    )


@pytest.mark.parametrize("phases_completed", range(1, 6))
def test_resume_from_every_phase_boundary(tmp_path, phases_completed: int) -> None:
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_engine(checkpointer)

    async def advance() -> None:
        for _ in range(phases_completed):
            await engine.step()

    asyncio.run(advance())

    expected_next_phase = PHASE_ORDER[phases_completed % len(PHASE_ORDER)]
    assert engine._state.phase is expected_next_phase

    resumed = _build_engine(checkpointer).from_checkpoint()
    assert resumed._state.phase is expected_next_phase
    assert resumed.iteration == (1 if phases_completed == 5 else 0)

    population = resumed.run()

    assert resumed.iteration == ITERATIONS
    assert population.get_genome_count() == POPULATION_SIZE
    for genome in population.population:
        assert genome.evaluation is not None


def test_offspring_survive_a_checkpoint_taken_mid_iteration(tmp_path) -> None:
    """Reproduce and mutate leave offspring in flight, which must be restored."""
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_engine(checkpointer)

    async def advance_to_mutate() -> None:
        await engine.step()
        await engine.step()

    asyncio.run(advance_to_mutate())
    original_offspring = [genome.phenotype for genome in engine.offspring_population.population]

    resumed = _build_engine(checkpointer).from_checkpoint()

    assert [genome.phenotype for genome in resumed.offspring_population.population] == original_offspring


def test_offspring_are_cleared_after_replacement(tmp_path) -> None:
    """Once offspring are promoted, a resumed engine must not still see them."""
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_engine(checkpointer)

    async def advance_through_replace() -> None:
        for _ in range(5):
            await engine.step()

    asyncio.run(advance_through_replace())

    resumed = _build_engine(checkpointer).from_checkpoint()

    assert resumed._state.offspring_population is None
    with pytest.raises(RuntimeError, match="unavailable before reproduction"):
        _ = resumed.offspring_population


def test_resuming_a_finished_run_does_no_further_work(tmp_path) -> None:
    """A completed run must be idempotent, not start an extra iteration."""
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    _build_engine(checkpointer).run()

    resumed = _build_engine(checkpointer).from_checkpoint()
    assert resumed.iteration == ITERATIONS

    resumed.run()
    assert resumed.iteration == ITERATIONS


def test_fitness_is_preserved_across_a_resume(tmp_path) -> None:
    """Restored genomes must keep their scores, or the run pays to rescore them."""
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_engine(checkpointer)

    asyncio.run(engine.step())
    original = [genome.evaluation for genome in engine.population.population]

    resumed = _build_engine(checkpointer).from_checkpoint()

    assert [genome.evaluation for genome in resumed.population.population] == original
