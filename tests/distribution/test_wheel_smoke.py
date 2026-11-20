"""Smoke the public engine API the way a wheel install would use it.

Example runners live in the checkout-only ``experiments/`` package, so this
file exercises ``ExperimentBuilder`` with a tiny inline genome instead. The
Distribution CI job copies this module outside the repository and runs it
against the built wheel, so an editable install cannot hide packaging mistakes.
"""

from __future__ import annotations

import importlib.resources
from typing import Self

import genai_opt
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Population,
    ReproductionPolicy,
    TerminalController,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
)
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation


class SmokeGenome(Genome[float, float]):
    """Minimal float genome for packaging smoke tests."""

    def __init__(self, phenotype: float, target: float = 50.0):
        super().__init__(phenotype)
        self.target = target

    async def invoke(self) -> Operation[float]:
        return Operation(self.phenotype)

    async def evaluate(self) -> Operation[float]:
        return Operation(100.0 - abs(self.invocation - self.target))

    async def mutate(self) -> Operation[Self]:
        return Operation(SmokeGenome(self.phenotype + 1.0, target=self.target))

    async def crossover(self, other: Self) -> Operation[Self]:
        mid = (self.phenotype + other.phenotype) / 2.0
        return Operation(SmokeGenome(mid, target=self.target))


def test_py_typed_ships_in_the_package() -> None:
    assert importlib.resources.files("genai_opt").joinpath("py.typed").is_file(), "py.typed missing from package"


def test_engine_runs_a_short_experiment() -> None:
    builder = ExperimentBuilder(
        inital_population_strategy=lambda: Population([SmokeGenome(float(i) * 10.0) for i in range(4)]),
        convergence_criterion=iteration_limited_convergence(2),
        mutation_policy=random_mutation(0.5),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(4),
            tournament_selection,
        ),
        experiment_controller=TerminalController(),
    )
    population = builder.build().run()
    _best, fitness = max(population.get_genome_fitness(), key=lambda item: item[1])

    assert population.get_genome_count() == 4
    assert fitness > 0
    assert genai_opt.__version__
