"""A metrics collector that prints one summary line per iteration."""

from __future__ import annotations

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector,
)
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class TerminalLoggerMetricsCollector(MetricsCollector[P, Inv]):
    """Prints a plain summary of one iteration's fitness spread and usage.

    Useful for summarizing metadata you already hold, such as the value returned
    by ``Engine.step()``. For live reporting during a run, pass a
    :class:`~genai_opt.optimizer_engine.experiment_controller.TerminalController`
    to the engine instead; the engine never calls collectors itself.
    """

    def collect(self, metadata: IterationMetadata[P, Inv]) -> None:
        """Print the iteration number, fitness spread, tokens and duration.

        Args:
            metadata: The iteration to summarize. An empty population prints just
                the iteration and a zero size rather than failing.
        """
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
