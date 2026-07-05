from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import I, P


class MetricsCollector(ABC, Generic[P, I]):
    @abstractmethod
    def collect(
        self,
        population: Population[P, I],
        iteration: int,
    ) -> None:
        raise NotImplementedError("MetricsCollector.collect() is not implemented")
