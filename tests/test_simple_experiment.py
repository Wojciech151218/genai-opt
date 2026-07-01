import asyncio

from genai_opt.experiments.simple_experiment import (
    TARGET_VALUE,
    run_simple_experiment,
)


def test_simple_experiment_improves_fitness() -> None:
    population = asyncio.run(
        run_simple_experiment(
            target=TARGET_VALUE,
            iterations=15,
            mutation_rate=0.3,
            population_size=30,
        )
    )

    best_genome, best_fitness = max(
        population.get_genome_fitness(),
        key=lambda item: item[1],
    )

    assert best_fitness > 70.0
    assert abs(best_genome.phenotype - TARGET_VALUE) < 30.0
