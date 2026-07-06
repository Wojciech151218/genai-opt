from __future__ import annotations

import time
from typing import Generic

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation_record import OperationRecord
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

    async def _mutate(self) -> list[OperationRecord]:
        operations: list[OperationRecord] = []
        for index, genome in enumerate(self.offspring_population.population):
            if self.mutation_policy(genome):
                start = time.perf_counter()
                mutated = await genome.mutate()
                duration = time.perf_counter() - start
                operations.append(
                    OperationRecord("mutation", duration, genome.last_operation_tokens)
                )
                genome._clear_operation_tokens()
                self.offspring_population.population[index] = mutated
        return operations

    async def _reproduce(self) -> tuple[Population[P, Inv], list[OperationRecord]]:
        return await self.reproduction_policy.get_new_population(self.population)

    async def _evaluate_offspring(self) -> list[OperationRecord]:
        return await self.offspring_population.evaluate_population()

    async def _evaluate_population(self) -> list[OperationRecord]:
        return await self.population.evaluate_population()

    def _replace(self) -> None:
        self.population = self.offspring_population

    def _clear_helper_populations(self) -> None:
        self.offspring_population = Population()

    async def run(self) -> Population[P, Inv]:
        while not self.convergence_criterion(self.population, self.iteration):
            self._clear_helper_populations()
            operations: list[OperationRecord] = []

            operations.extend(await self._evaluate_population())
            self.offspring_population, reproduction_operations = await self._reproduce()
            operations.extend(reproduction_operations)
            operations.extend(await self._mutate())
            operations.extend(await self._evaluate_offspring())
            self._replace()

            metadata = IterationMetadata.from_population(
                iteration=self.iteration,
                population=self.population,
                operations=operations,
            )
            self.metrics_collector.collect(metadata)
            self.iteration += 1

        return self.population
