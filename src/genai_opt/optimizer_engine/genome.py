from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Self

from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Genome(ABC, Generic[P, Inv]):
    def __init__(self, phenotype: P):
        self.phenotype = phenotype
        self._evaluation: float | None = None
        self._invocation: Inv | None = None
        self._last_operation_tokens: int = 0

    @property
    def invocation(self) -> Inv:
        if self._invocation is None:
            raise ValueError("Genome has not been invoked")
        return self._invocation

    @property
    def evaluation(self) -> float:
        if self._evaluation is None:
            raise ValueError("Genome has not been evaluated")
        return self._evaluation

    def reset_invocations(self) -> None:
        self._invocation = None

    def _set_invocation(self, invocation: Inv) -> None:
        self._invocation = invocation

    def reset_evaluation(self) -> None:
        self._evaluation = None

    def _set_evaluation(self, value: float) -> None:
        self._evaluation = value

    @property
    def last_operation_tokens(self) -> int:
        return self._last_operation_tokens

    def _set_operation_tokens(self, tokens: int) -> None:
        self._last_operation_tokens = tokens

    def _clear_operation_tokens(self) -> None:
        self._last_operation_tokens = 0

    @abstractmethod
    async def invoke(self) -> Inv:
        raise NotImplementedError("Genome.invoke() is not implemented")

    @abstractmethod
    async def evaluate(self) -> float:
        raise NotImplementedError("Genome.evaluate() is not implemented")

    async def _evaluate(self) -> None:
        self._set_evaluation(await self.evaluate())

    async def _invoke(self) -> None:
        self._set_invocation(await self.invoke())

    @abstractmethod
    async def mutate(self) -> Self:
        raise NotImplementedError("Genome.mutate() is not implemented")

    @abstractmethod
    async def crossover(self, other: Genome[P, Inv]) -> Self:
        raise NotImplementedError("Genome.crossover() is not implemented")
