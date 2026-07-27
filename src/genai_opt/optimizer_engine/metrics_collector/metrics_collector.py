from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class MetricsCollector(ABC, Generic[P, Inv]):
    @abstractmethod
    def collect(self, metadata: IterationMetadata[P, Inv]) -> None:
        raise NotImplementedError("MetricsCollector.collect() is not implemented")
