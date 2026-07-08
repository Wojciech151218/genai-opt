from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Generic, Self

from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Genome(ABC, Generic[P, Inv]):
    def __init__(self, phenotype: P):
        self.phenotype = phenotype
        self._evaluation: float | None = None
        self._invocation: Inv | None = None

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

    @abstractmethod
    async def invoke(self) -> Operation[Inv]:
        raise NotImplementedError("Genome.invoke() is not implemented")

    @abstractmethod
    async def evaluate(self) -> Operation[float]:
        raise NotImplementedError("Genome.evaluate() is not implemented")

    @abstractmethod
    async def mutate(self) -> Operation[Self]:
        raise NotImplementedError("Genome.mutate() is not implemented")

    @abstractmethod
    async def crossover(self, other: Genome[P, Inv]) -> Operation[Self]:
        raise NotImplementedError("Genome.crossover() is not implemented")

    @staticmethod
    async def _timed(operation_coroutine, kind: OperationKind) -> Operation:
        start = time.perf_counter()
        operation = await operation_coroutine
        duration = time.perf_counter() - start
        operation.set_kind(kind)
        if operation.duration_seconds == 0.0:
            operation.set_duration(duration)
        return operation

    async def _invoke(self) -> Operation[Inv]:
        operation = await self._timed(self.invoke(), "invoke")
        self._set_invocation(operation.value)
        return operation

    async def _evaluate(self) -> Operation[float]:
        operation = await self._timed(self.evaluate(), "evaluate")
        self._set_evaluation(operation.value)
        return operation

    async def _mutate(self) -> Operation[Self]:
        return await self._timed(self.mutate(), "mutation")

    async def _crossover(self, other: Genome[P, Inv]) -> Operation[Self]:
        return await self._timed(self.crossover(other), "crossover")
