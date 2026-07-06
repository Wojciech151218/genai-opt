from __future__ import annotations

import asyncio
from typing import Generic

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import (
    ReproductionPolicy,
)
from genai_opt.optimizer_engine.utils.types import Types as T
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Engine(Generic[P, Inv]):
    def __init__(
        self,
        population: Population[P, Inv],
        convergence_criterion: T.ConvergenceCriterion,
        mutation_policy: T.MutationPolicy,
        reproduction_policy: ReproductionPolicy,
        metrics_collector: T.MetricsCollector,
    ):
        self.population: Population[P, Inv] = population
        self.offspring_population: Population[P, Inv] = Population()
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
        self.offspring_population = await self.reproduction_policy.get_new_population(self.population)

    async def _evaluate_offspring(self) -> None:
        await self.offspring_population.evaluate_population()

    async def _evaluate_population(self) -> None:
        await self.population.evaluate_population()

    def _replace(self) -> None:
        self.population = self.offspring_population

    def _clear_helper_populations(self) -> None:
        self.offspring_population = Population()

    def run(self) -> Population[P, Inv]:
        return asyncio.run(self._run_async())

    async def _run_async(self) -> Population[P, Inv]:
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
