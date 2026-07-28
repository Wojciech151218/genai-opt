from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class MetricsCollector(ABC, Generic[P, Inv]):
    """Turns one iteration's metadata into a report.

    Collectors are a standalone reporting helper: the engine never calls them.
    Live reporting during a run belongs to
    :class:`~genai_opt.optimizer_engine.experiment_controller.ExperimentController`,
    which receives every phase and every operation as it happens. Reach for a
    collector when you want to summarize an
    :class:`~genai_opt.optimizer_engine.iteration_metadata.IterationMetadata`
    you already hold, for example the value returned by ``Engine.step()`` or
    one read back from a checkpoint.
    """

    @abstractmethod
    def collect(self, metadata: IterationMetadata[P, Inv]) -> None:
        """Report a single iteration's metadata.

        Args:
            metadata: Statistics and operations gathered for one phase.
        """
        raise NotImplementedError("MetricsCollector.collect() is not implemented")
