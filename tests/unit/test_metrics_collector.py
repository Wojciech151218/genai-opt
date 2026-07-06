"""Tests for TerminalLoggerMetricsCollector."""

import asyncio

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.metrics_collector.terminal_logger import (
    TerminalLoggerMetricsCollector,
)
from genai_opt.optimizer_engine.population import Population


def test_terminal_logger_prints_stats(capsys):
    """Collect should print best, worst, iteration, and population_size."""
    pop = Population()
    pop.add_genome(FloatGenome(50.0, target=50.0))  # fitness = 100.0
    pop.add_genome(FloatGenome(40.0, target=50.0))  # fitness = 90.0
    asyncio.run(pop.evaluate_population())

    TerminalLoggerMetricsCollector().collect(pop, iteration=0)

    captured = capsys.readouterr().out
    assert "best=100.0000" in captured
    assert "worst=90.0000" in captured
    assert "iteration=0" in captured
    assert "population_size=2" in captured


def test_terminal_logger_empty_population(capsys):
    """Collect with empty population should still print iteration and size."""
    TerminalLoggerMetricsCollector().collect(Population(), iteration=5)

    captured = capsys.readouterr().out
    assert "iteration=5" in captured
    assert "population_size=0" in captured
