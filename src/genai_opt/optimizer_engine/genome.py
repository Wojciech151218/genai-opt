from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, TypeVar

PHENOTYPE = TypeVar('PHENOTYPE')
INVOCATION = TypeVar('INVOCATION')

class Genome(ABC):
    def __init__(self, phenotype: PHENOTYPE):
        self.phenotype = phenotype
        self._evaluation: float | None = None
        self._invocations: INVOCATION | None = None
    @property
    def evaluation(self) -> float:
        if self._evaluation is None:
            raise ValueError("Genome has not been evaluated")
        return self._evaluation

    def reset_evaluation(self) -> None:
        self._evaluation = None

    def _set_evaluation(self, value: float) -> None:
        self._evaluation = value

    @abstractmethod
    async def invoke(self) -> INVOCATION:
        raise NotImplementedError("Genome.invoke() is not implemented")

    @abstractmethod
    async def evaluate(self) -> None:
        raise NotImplementedError("Genome.evaluate() is not implemented")

    @abstractmethod
    async def mutate(self) -> Self:
        raise NotImplementedError("Genome.mutate() is not implemented")

    @abstractmethod
    async def crossover(self, other: 'Genome[PHENOTYPE,INVOCATION]') -> Self:
        raise NotImplementedError("Genome.crossover() is not implemented")