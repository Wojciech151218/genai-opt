import asyncio

from genai_opt.experiments.simple_experiment import run_simple_experiment


def test_population_size_one():
    """Engine should handle a population of size 1 without errors."""
    result = asyncio.run(
        run_simple_experiment(population_size=1, iterations=5, mutation_rate=0.5)
    )
    assert result.get_genome_count() >= 1, "Population should have at least 1 genome"


def test_zero_iterations():
    """With 0 iterations the engine should return the initial population unchanged."""
    population_size = 10
    result = asyncio.run(
        run_simple_experiment(iterations=0, population_size=population_size)
    )
    assert result.get_genome_count() == population_size, (
        f"Expected {population_size} genomes, got {result.get_genome_count()}"
    )


def test_mutation_rate_zero():
    """Mutation rate of 0.0 should complete without errors (no mutations applied)."""
    result = asyncio.run(
        run_simple_experiment(mutation_rate=0.0, iterations=5, population_size=10)
    )
    assert result.get_genome_count() > 0


def test_mutation_rate_one():
    """Mutation rate of 1.0 should complete without errors (all genomes mutated)."""
    result = asyncio.run(
        run_simple_experiment(mutation_rate=1.0, iterations=5, population_size=10)
    )
    assert result.get_genome_count() > 0
