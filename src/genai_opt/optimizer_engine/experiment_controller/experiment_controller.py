"""The controller contract and its do-nothing default."""

from __future__ import annotations

from abc import ABC, abstractmethod

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation


class ExperimentController(ABC):
    """Observes a running experiment and can pause it.

    Controllers are the live view of a run: the engine reports each phase and,
    where it can, each individual operation as it completes. That is what makes
    a slow LLM-backed generation observable while it is still in progress, and
    it is why reporting belongs here rather than in a
    :class:`~genai_opt.optimizer_engine.metrics_collector.metrics_collector.MetricsCollector`.

    Pausing is cooperative. Setting the flag makes the engine wait at the start
    of its next phase; it never interrupts work already in flight.
    """

    def __init__(self) -> None:
        self._paused = False

    def is_paused(self) -> bool:
        """Whether the engine should hold before starting its next phase."""
        return self._paused

    def pause(self) -> None:
        """Ask the engine to stop before its next phase."""
        self._paused = True

    def resume(self) -> None:
        """Let a paused engine continue."""
        self._paused = False

    @abstractmethod
    async def setup(self) -> None:
        """Prepare for a run, before the first phase.

        Anything claimed here should be released in :meth:`teardown`.
        """
        raise NotImplementedError("ExperimentController.setup() is not implemented")

    async def teardown(self) -> None:
        """Release anything claimed by :meth:`setup`.

        The engine calls this once a run finishes, including when it fails, so
        controllers that start background tasks or grab terminal state can let
        go of them. Defaults to doing nothing.
        """
        return None

    @abstractmethod
    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        """Receive a phase's results once it finishes.

        Called once per phase, so five times per iteration.

        Args:
            iteration_metadata: What the phase produced, including its
                operations and the fitness spread of the population it touched.
        """
        raise NotImplementedError("ExperimentController.control_iteration() is not implemented")

    async def control_operation(self, iteration: int, phase: IterationPhase, operation: Operation) -> None:
        """Receive an operation as it becomes available within a phase.

        During evaluation these arrive as genomes finish, so progress is visible
        before the phase ends. Reproduction and mutation report theirs once the
        phase completes. Defaults to doing nothing.

        Args:
            iteration: The iteration in progress.
            phase: The phase in progress.
            operation: The completed operation.
        """
        return None


class NullExperimentController(ExperimentController):
    """Reports nothing and never pauses. The engine's default."""

    async def setup(self) -> None:
        """Do nothing."""

    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        """Ignore the phase results."""
