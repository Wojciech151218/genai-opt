from __future__ import annotations

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector,
)
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class TerminalLoggerMetricsCollector(MetricsCollector[P, Inv]):
    def collect(self, metadata: IterationMetadata[P, Inv]) -> None:
        fitnesses = [state.fitness for state in metadata.phenotype_states if state.fitness is not None]
        population_size = len(metadata.phenotype_states)

        if population_size == 0:
            print(f"iteration={metadata.iteration} population_size=0")
            return

        best = max(fitnesses)
        worst = min(fitnesses)
        mean = sum(fitnesses) / len(fitnesses)
        print(
            f"iteration={metadata.iteration} population_size={population_size} "
            f"best={best:.4f} worst={worst:.4f} mean={mean:.4f} "
            f"tokens={metadata.total_tokens} "
            f"duration={metadata.total_duration_seconds:.4f}s"
        )
