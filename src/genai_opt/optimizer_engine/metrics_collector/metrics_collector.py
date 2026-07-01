from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from genai_opt.optimizer_engine.population import Population

INVOCATION = TypeVar('INVOCATION')
PHENOTYPE = TypeVar('PHENOTYPE')


class MetricsCollector(ABC):
    @abstractmethod
    def collect(
        self,
        population: Population[PHENOTYPE, INVOCATION],
        iteration: int,
    ) -> None:
        raise NotImplementedError("MetricsCollector.collect() is not implemented")
