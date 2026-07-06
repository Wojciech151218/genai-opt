import asyncio

from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import iteration_limited_convergence
from genai_opt.optimizer_engine.mutation_policy.mutation_policy import random_mutation
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import ReproductionPolicy
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import generational_reproduction
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import tournament_selection
from genai_opt.optimizer_engine.metrics_collector.terminal_logger import TerminalLoggerMetricsCollector
from genai_opt.optimizer_engine.population import Population
from genai_opt.experiments.float_genome import FloatGenome


def _build_test_engine(iterations=5):
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
    metrics_collector = TerminalLoggerMetricsCollector()

    return Engine(
        population=population,
        convergence_criterion=convergence_criterion,
        mutation_policy=mutation_policy,
        reproduction_policy=reproduction_policy,
        metrics_collector=metrics_collector,
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
