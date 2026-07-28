"""The optimization loop itself."""

from __future__ import annotations

import asyncio
from typing import Any, Generic, Self

from genai_opt.optimizer_engine.checkpointer import Checkpointer, NullCheckpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
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
    """Runs a population through evolutionary iterations until it converges.

    Each iteration is split into the five phases of
    :class:`~genai_opt.optimizer_engine.engine_state.IterationPhase`, and one
    phase is executed per call to :meth:`step`. That granularity is what makes a
    run resumable: a checkpoint is saved after every phase, so an interrupted
    LLM-backed experiment never has to repeat work it already paid for.

    Call :meth:`run` for the usual blocking loop, or drive :meth:`step`
    yourself when you want control over scheduling.

    Args:
        population: The starting population.
        convergence_criterion: Called with the population and the iteration
            number at the top of each iteration; returning ``True`` stops the
            run.
        mutation_policy: Decides, per offspring genome, whether to mutate it.
        reproduction_policy: Produces the offspring population from the current
            one.
        checkpointer: Persists state after every phase. Defaults to
            :class:`~genai_opt.optimizer_engine.checkpointer.NullCheckpointer`,
            which keeps nothing.
        experiment_controller: Observes phases and operations, and can pause the
            run. Defaults to
            :class:`~genai_opt.optimizer_engine.experiment_controller.NullExperimentController`.
    """

    def __init__(
        self,
        population: Population[P, Inv],
        convergence_criterion: T.ConvergenceCriterion,
        mutation_policy: T.MutationPolicy,
        reproduction_policy: ReproductionPolicy,
        checkpointer: Checkpointer[P, Inv] | None = None,
        experiment_controller: ExperimentController | None = None,
    ):
        self._state = EngineState(population=population)

        self.reproduction_policy = reproduction_policy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy
        self.checkpointer = checkpointer or NullCheckpointer()
        self.experiment_controller = experiment_controller or NullExperimentController()

    @property
    def population(self) -> Population[P, Inv]:
        """The current generation."""
        return self._state.population

    @population.setter
    def population(self, population: Population[P, Inv]) -> None:
        self._state.population = population

    @property
    def offspring_population(self) -> Population[P, Inv]:
        """The candidate next generation.

        Raises:
            RuntimeError: If accessed before the reproduce phase has run, or
                after the offspring have replaced the current population.
        """
        if self._state.offspring_population is None:
            raise RuntimeError("Offspring population is unavailable before reproduction")
        return self._state.offspring_population

    @offspring_population.setter
    def offspring_population(self, population: Population[P, Inv]) -> None:
        self._state.offspring_population = population

    @property
    def iteration(self) -> int:
        """How many complete iterations have finished."""
        return self._state.iteration

    @iteration.setter
    def iteration(self, iteration: int) -> None:
        self._state.iteration = iteration

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

    async def _evaluate_and_stream(
        self,
        population: Population[P, Inv],
        phase: IterationPhase,
    ) -> list[Operation]:
        operations: list[Operation] = []
        async for operation in population.evaluate_population_stream():
            operations.append(operation)
            await self.experiment_controller.control_operation(self.iteration, phase, operation)
        return operations

    async def _stream_operations(self, phase: IterationPhase, operations: list[Operation]) -> None:
        for operation in operations:
            await self.experiment_controller.control_operation(self.iteration, phase, operation)

    def _replace(self) -> None:
        self.population = self.offspring_population
        self._state.offspring_population = None

    def _clear_helper_populations(self) -> None:
        self._state.offspring_population = None

    def get_population(self) -> Population[P, Inv]:
        """Return the current generation."""
        return self.population

    def from_checkpoint(self, **context: Any) -> Self:
        """Restore saved state from the configured checkpointer, if any exists.

        Safe to call on a fresh run: when no checkpoint is found the engine
        keeps the population it was built with, so the usual
        ``builder.build().from_checkpoint()`` chain works either way.

        Args:
            **context: Passed through to the checkpointer, which forwards it to
                each genome's deserializer. Genomes that hold non-serializable
                collaborators, such as a chat model or an evaluation function,
                are rebuilt from these values.

        Returns:
            This engine, to allow chaining.
        """
        state = self.checkpointer.load(**context)
        if state is not None:
            self._state = state
        return self

    def _clear_operations(self) -> None:
        self._state.iteration_operations = []

    async def _collect_metadata_and_control(
        self,
        operations: list[Operation],
        population: Population[P, Inv],
        phase: IterationPhase,
    ) -> IterationMetadata[P, Inv]:
        self._state.iteration_operations.extend(operations)
        iteration_metadata = IterationMetadata.from_population(
            iteration=self.iteration,
            population=population,
            operations=operations,
            phase=phase,
        )
        await self.experiment_controller.control_iteration(iteration_metadata)
        return iteration_metadata

    async def _wait_if_paused(self) -> None:
        while self.experiment_controller.is_paused():
            await asyncio.sleep(0.1)

    def _save_checkpoint(self, metadata: IterationMetadata[P, Inv]) -> None:
        self.checkpointer.save_checkpoint(self._state, metadata)

    async def step(self) -> IterationMetadata[P, Inv]:
        """Execute and persist one phase of the current iteration.

        Blocks while the experiment controller reports a paused run, advances
        the stored phase, notifies the controller, then checkpoints. Because the
        stored phase is always the *next* one to execute, a checkpoint written
        here can be resumed without repeating the phase that produced it.

        Returns:
            Metadata for the phase that just ran, including its operations and
            the fitness spread of the population it touched.

        Raises:
            RuntimeError: If the stored phase is not a recognized
                :class:`~genai_opt.optimizer_engine.engine_state.IterationPhase`,
                which normally means a checkpoint from an incompatible version.
        """
        await self._wait_if_paused()
        phase = self._state.phase

        if phase is IterationPhase.EVALUATE_POPULATION:
            self._clear_helper_populations()
            self._clear_operations()
            operations = await self._evaluate_and_stream(self.population, phase)
            self._state.phase = IterationPhase.REPRODUCE
            metadata = await self._collect_metadata_and_control(operations, self.population, phase)
        elif phase is IterationPhase.REPRODUCE:
            offspring, operations = await self._reproduce()
            await self._stream_operations(phase, operations)
            self.offspring_population = offspring
            self._state.phase = IterationPhase.MUTATE
            metadata = await self._collect_metadata_and_control(operations, offspring, phase)
        elif phase is IterationPhase.MUTATE:
            operations = await self._mutate()
            await self._stream_operations(phase, operations)
            self._state.phase = IterationPhase.EVALUATE_OFFSPRING
            metadata = await self._collect_metadata_and_control(operations, self.offspring_population, phase)
        elif phase is IterationPhase.EVALUATE_OFFSPRING:
            operations = await self._evaluate_and_stream(self.offspring_population, phase)
            self._state.phase = IterationPhase.REPLACE
            metadata = await self._collect_metadata_and_control(operations, self.offspring_population, phase)
        elif phase is IterationPhase.REPLACE:
            self._replace()
            self.iteration += 1
            self._state.phase = IterationPhase.EVALUATE_POPULATION
            metadata = await self._collect_metadata_and_control([], self.population, phase)
        else:
            raise RuntimeError(f"Unsupported engine phase: {phase}")

        self._save_checkpoint(metadata)
        return metadata

    def run(self) -> Population[P, Inv]:
        """Iterate until the convergence criterion is satisfied.

        This is the synchronous entry point and it owns the event loop, so it
        cannot be called from inside one. Await :meth:`step` in a loop instead
        if you already have a running loop.

        Returns:
            The final population, with every genome evaluated.
        """
        return asyncio.run(self._run_async())

    async def _run_async(self) -> Population[P, Inv]:
        await self.experiment_controller.setup()
        try:
            while self._state.phase is not IterationPhase.EVALUATE_POPULATION or not self.convergence_criterion(
                self.population, self.iteration
            ):
                await self.step()
            return self.population
        finally:
            await self.experiment_controller.teardown()
