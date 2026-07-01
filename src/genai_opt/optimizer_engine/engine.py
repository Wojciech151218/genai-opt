from __future__ import annotations

from typing import Callable, TypeVar

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector,
)
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import (
    ReproductionPolicy,
)

INVOCATION = TypeVar("INVOCATION")
PHENOTYPE = TypeVar("PHENOTYPE")


class Engine:
    def __init__(
        self,
        population: Population[PHENOTYPE, INVOCATION],
        convergence_criterion: Callable[
            [Population[PHENOTYPE, INVOCATION], int], bool
        ],
        mutation_policy: Callable[[Genome[PHENOTYPE, INVOCATION]], bool],
        reproduction_policy: ReproductionPolicy,
        metrics_collector: MetricsCollector,
    ):
        self.population: Population[PHENOTYPE, INVOCATION] = population
        self.offspring_population: Population[PHENOTYPE, INVOCATION] = Population()
        self.iteration: int = 0

        self.metrics_collector = metrics_collector
        self.reproduction_policy = reproduction_policy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy

    async def _mutate(self) -> None:
        for index, genome in enumerate(self.offspring_population.population):
            if self.mutation_policy(genome):
                self.offspring_population.population[index] = await genome.mutate()

    async def _reproduce(self) -> None:
        self.offspring_population = await self.reproduction_policy.get_new_population(
            self.population
        )

    async def _evaluate_offspring(self) -> None:
        await self.offspring_population.evaluate_population()

    async def _evaluate_population(self) -> None:
        await self.population.evaluate_population()

    def _replace(self) -> None:
        self.population = self.offspring_population

    def _clear_helper_populations(self) -> None:
        self.offspring_population = Population()

    async def run(self) -> Population[PHENOTYPE, INVOCATION]:
        while not self.convergence_criterion(self.population, self.iteration):
            self._clear_helper_populations()

            await self._evaluate_population()
            await self._reproduce()
            await self._mutate()
            await self._evaluate_offspring()
            self._replace()
            self.metrics_collector.collect(self.population, self.iteration)
            self.iteration += 1

        return self.population
