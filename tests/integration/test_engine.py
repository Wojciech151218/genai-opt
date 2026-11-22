import asyncio

from experiments.float_genome import FloatGenome

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


def _build_test_engine(iterations=5, checkpointer=None, reuse_evaluations=False):
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
        reuse_evaluations=reuse_evaluations,
    )


def test_full_engine_run():
    """Build a complete engine manually and verify it runs end-to-end."""
    engine = _build_test_engine(iterations=5)
    result = engine.run()

    assert result.get_genome_count() > 0, "Returned population should have genomes"
    for genome in result.population:
        # Accessing evaluation should not raise ValueError if genome was evaluated
        _ = genome.evaluation


def test_experiment_convergence():
    """Engine should stop after exactly the configured number of iterations."""
    engine = _build_test_engine(iterations=3)
    engine.run()

    assert engine.iteration == 3, f"Expected 3 iterations, got {engine.iteration}"


def test_engine_reuses_offspring_evaluations_at_next_iteration():
    """With reuse enabled, evaluated children are not invoked a second time."""
    engine = _build_test_engine(iterations=2, reuse_evaluations=True)

    async def run_first_iteration() -> tuple[list[float], list[float]]:
        # Evaluate initial population, reproduce and mutate children, then score them.
        await engine.step()
        await engine.step()
        await engine.step()
        await engine.step()
        offspring_invocations = [genome.invocation for genome in engine.offspring_population.population]
        offspring_fitnesses = [genome.evaluation for genome in engine.offspring_population.population]
        await engine.step()  # Replace the current population with those scored children.
        return offspring_invocations, offspring_fitnesses

    invocations, fitnesses = asyncio.run(run_first_iteration())
    operations = asyncio.run(engine.step())

    assert engine._state.phase is IterationPhase.REPRODUCE
    assert operations.operations == []
    assert [genome.invocation for genome in engine.population.population] == invocations
    assert [genome.evaluation for genome in engine.population.population] == fitnesses


def test_engine_resumes_from_a_phase_checkpoint(tmp_path):
    """A resumed engine continues at the saved phase without redoing it."""
    checkpointer = FilesystemCheckpointer(tmp_path)
    engine = _build_test_engine(iterations=3, checkpointer=checkpointer)

    asyncio.run(engine.step())
    asyncio.run(engine.step())
    assert engine._state.phase is IterationPhase.MUTATE

    resumed_engine = _build_test_engine(iterations=3, checkpointer=checkpointer).from_checkpoint()
    assert resumed_engine._state.phase is IterationPhase.MUTATE

    result = resumed_engine.run()
    assert resumed_engine.iteration == 3
    assert result.get_genome_count() == 10
