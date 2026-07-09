from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Checkpointer(ABC, Generic[P, Inv]):
    @abstractmethod
    def save_checkpoint(
        self,
        population: Population[P, Inv],
        iteration: int,
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        raise NotImplementedError("Checkpointer.save_checkpoint() is not implemented")

    @abstractmethod
    def load(self) -> tuple[Population[P, Inv], int] | None:
        raise NotImplementedError("Checkpointer.load() is not implemented")


class NullCheckpointer(Checkpointer[P, Inv]):
    def save_checkpoint(
        self,
        population: Population[P, Inv],
        iteration: int,
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        pass

    def load(self) -> tuple[Population[P, Inv], int] | None:
        return None
