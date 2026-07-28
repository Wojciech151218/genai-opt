from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

from genai_opt.optimizer_engine.genome import Genome as Gen
from genai_opt.optimizer_engine.iteration_metadata import (
    IterationMetadata as IM,
)
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector as MC,
)
from genai_opt.optimizer_engine.operation import Operation as Op
from genai_opt.optimizer_engine.population import Population as Pop
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Types:
    """Short aliases for the engine's recurring generic types.

    Imported as ``T`` throughout the engine so signatures stay readable, for
    example ``def random_mutation(threshold: float) -> T.MutationPolicy``.
    """

    Genome: TypeAlias = Gen[P, Inv]
    IterationMetadata: TypeAlias = IM[P, Inv]
    MetricsCollector: TypeAlias = MC[P, Inv]
    Operation: TypeAlias = Op[Any]
    Population: TypeAlias = Pop[P, Inv]
    ParentPair: TypeAlias = tuple[Gen[P, Inv], Gen[P, Inv]]

    ConvergenceCriterion: TypeAlias = Callable[[Pop[P, Inv], int], bool]
    InitialPopulationStrategy: TypeAlias = Callable[..., Pop[P, Inv]]
    MutationPolicy: TypeAlias = Callable[[Gen[P, Inv]], bool]
    ParentSelection: TypeAlias = Callable[[Pop[P, Inv]], ParentPair]
    ReproduceFn: TypeAlias = Callable[
        [Pop[P, Inv]],
        tuple[Pop[P, Inv], list[Op[Any]]] | Awaitable[tuple[Pop[P, Inv], list[Op[Any]]]],
    ]
    ReproductionStrategy: TypeAlias = Callable[[ParentSelection], ReproduceFn]
