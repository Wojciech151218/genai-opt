from __future__ import annotations

from abc import ABC, abstractmethod

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation


class ExperimentController(ABC):
    def __init__(self) -> None:
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @abstractmethod
    async def setup(self) -> None:
        raise NotImplementedError("ExperimentController.setup() is not implemented")

    @abstractmethod
    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        raise NotImplementedError("ExperimentController.control_iteration() is not implemented")

    async def control_operation(self, iteration: int, phase: IterationPhase, operation: Operation) -> None:
        """Receive an operation as it becomes available within a phase."""
        return None


class NullExperimentController(ExperimentController):
    async def setup(self) -> None:
        pass

    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        pass
