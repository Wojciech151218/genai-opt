from __future__ import annotations

from abc import ABC, abstractmethod

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata


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


class NullExperimentController(ExperimentController):
    async def setup(self) -> None:
        pass

    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        pass
