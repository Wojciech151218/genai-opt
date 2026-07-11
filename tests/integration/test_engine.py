import asyncio

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.checkpointer import FilesystemCheckpointer
from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import (
    iteration_limited_convergence,
)
from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.experiment_controller import NullExperimentController
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


def _build_test_engine(iterations=5, checkpointer=None):
    """Helper to build a complete engine with FloatGenome population."""
    target = 50.0
    genomes = [FloatGenome(phenotype=float(v), target=target) for v in range(10, 110, 10)]
    population = Population(genomes)

    convergence_criterion = iteration_limited_convergence(iterations)
    mutation_policy = random_mutation(0.3)
    reproduction_policy = ReproductionPolicy(
        generational_reproduction(10),
        tournament_selection,
    )
    return Engine(
        population=population,
        convergence_criterion=convergence_criterion,
        mutation_policy=mutation_policy,
        reproduction_policy=reproduction_policy,
        checkpointer=checkpointer,
        experiment_controller=NullExperimentController(),
    )


def test_full_engine_run():
    """Build a complete engine manually and verify it runs end-to-end."""
    engine = _build_test_engine(iterations=5)
    result = asyncio.run(engine.run())

    assert result.get_genome_count() > 0, "Returned population should have genomes"
    for genome in result.population:
        # Accessing evaluation should not raise ValueError if genome was evaluated
        _ = genome.evaluation


def test_experiment_convergence():
    """Engine should stop after exactly the configured number of iterations."""
    engine = _build_test_engine(iterations=3)
    asyncio.run(engine.run())

    assert engine.iteration == 3, f"Expected 3 iterations, got {engine.iteration}"


def test_engine_resumes_from_a_phase_checkpoint(tmp_path):
    """A resumed engine continues at the saved phase without redoing it."""
    checkpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_test_engine(iterations=3, checkpointer=checkpointer)

    asyncio.run(engine.step())
    asyncio.run(engine.step())
    assert engine._state.phase is IterationPhase.MUTATE

    resumed_engine = _build_test_engine(iterations=3, checkpointer=checkpointer).from_checkpoint()
    assert resumed_engine._state.phase is IterationPhase.MUTATE

    result = asyncio.run(resumed_engine.run())
    assert resumed_engine.iteration == 3
    assert result.get_genome_count() == 10
