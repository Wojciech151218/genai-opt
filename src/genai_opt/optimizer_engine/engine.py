from __future__ import annotations

import asyncio
from typing import Generic, Self

from genai_opt.optimizer_engine.checkpointer import Checkpointer, NullCheckpointer
from genai_opt.optimizer_engine.experiment_controller import ExperimentController, NullExperimentController
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
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
        checkpointer: Checkpointer[P, Inv] | None = None,
        experiment_controller: ExperimentController | None = None,
    ):
        self.population: T.Population = population
        self.offspring_population: Population[P, Inv] = Population()
        self.iteration: int = 0

        self.reproduction_policy = reproduction_policy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy
        self.checkpointer = checkpointer or NullCheckpointer()
        self.experiment_controller = experiment_controller or NullExperimentController()
        self.iteration_operations: list[Operation] = []

    async def _mutate(self) -> list[Operation]:
        operations: list[Operation] = []
        for index, genome in enumerate(self.offspring_population.population):
            if self.mutation_policy(genome):
                operation = await genome._mutate()
                operations.append(operation)
                self.offspring_population.population[index] = operation.value
        return operations

    async def _reproduce(self) -> tuple[Population[P, Inv], list[Operation]]:
        return await self.reproduction_policy.get_new_population(self.population)

    async def _evaluate_offspring(self) -> list[Operation]:
        return await self.offspring_population.evaluate_population()

    async def _evaluate_population(self) -> list[Operation]:
        return await self.population.evaluate_population()

    def _replace(self) -> None:
        self.population = self.offspring_population

    def _clear_helper_populations(self) -> None:
        self.offspring_population = Population()

    def get_population(self) -> Population[P, Inv]:
        return self.population

    def from_checkpoint(self, **context) -> Self:
        checkpoint = self.checkpointer.load(**context)
        if checkpoint is not None:
            checkpoint_population, checkpoint_iteration = checkpoint
            self.population = checkpoint_population
            self.iteration = checkpoint_iteration
        return self

    def _clear_operations(self) -> None:
        self.iteration_operations = []

    async def _collect_metadata_and_control(self, operations: list[Operation]) -> IterationMetadata[P, Inv]:
        self.iteration_operations.extend(operations)
        iteration_metadata = IterationMetadata.from_population(
            iteration=self.iteration,
            population=self.population,
            operations=operations,
        )
        await self.experiment_controller.control_iteration(iteration_metadata)
        return iteration_metadata

    async def _wait_if_paused(self) -> None:
        while self.experiment_controller.is_paused():
            await asyncio.sleep(0.1)

    async def run(self) -> Population[P, Inv]:
        # @TODO allow for streaming operations to the the controller and make it possiblre
        # to checpoint in between iterations, make the iteration process work like a state machine
        await self.experiment_controller.setup()

        while not self.convergence_criterion(self.population, self.iteration):
            await self._wait_if_paused()
            self._clear_helper_populations()
            await self._wait_if_paused()

            await self._collect_metadata_and_control(await self._evaluate_population())
            await self._wait_if_paused()
            self.offspring_population, reproduction_operations = await self._reproduce()
            await self._collect_metadata_and_control(reproduction_operations)
            await self._wait_if_paused()
            await self._collect_metadata_and_control(await self._mutate())
            await self._wait_if_paused()
            iteration_metadata = await self._collect_metadata_and_control(await self._evaluate_offspring())
            await self._wait_if_paused()
            self._replace()
            self.iteration += 1
            self.checkpointer.save_checkpoint(self.population, self.iteration, iteration_metadata)

        return self.population
