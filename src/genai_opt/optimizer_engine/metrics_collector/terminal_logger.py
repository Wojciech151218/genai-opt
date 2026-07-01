from __future__ import annotations

from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    INVOCATION,
    PHENOTYPE,
    MetricsCollector,
)
from genai_opt.optimizer_engine.population import Population


class TerminalLoggerMetricsCollector(MetricsCollector):
    def collect(
        self,
        population: Population[PHENOTYPE, INVOCATION],
        iteration: int,
    ) -> None:
        fitnesses = [fitness for _, fitness in population.get_genome_fitness()]
        population_size = len(fitnesses)

        if population_size == 0:
            print(f"iteration={iteration} population_size=0")
            return

        best = max(fitnesses)
        worst = min(fitnesses)
        mean = sum(fitnesses) / population_size
        print(
            f"iteration={iteration} "
            f"population_size={population_size} "
            f"best={best:.4f} "
            f"worst={worst:.4f} "
            f"mean={mean:.4f}"
        )
