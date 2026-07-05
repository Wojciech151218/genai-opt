from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from genai_opt.optimizer_engine.genome import Genome as Gen
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector as MC,
)
from genai_opt.optimizer_engine.population import Population as Pop

P = TypeVar("PHENOTYPE")
I = TypeVar("INVOCATION")

type ParentPair[P, I] = tuple[Gen[P, I], Gen[P, I]]


class Types:
    type Genome = Gen[P, I]
    type Population = Pop[P, I]
    type ConvergenceCriterion = Callable[[Population[P, I], int], bool]
    type InitialPopulationStrategy = Callable[[Any, ...], Pop[P, I]]
    type MetricsCollector = MC[P, I]
    type MutationPolicy = Callable[[Gen[P, I]], bool]
    type ParentSelection = Callable[[Pop[P, I]], ParentPair[P, I]]
    type ReproduceFn = Callable[
        [Pop[P, I]], Pop[P, I] | Awaitable[Pop[P, I]]
    ]
    type ReproductionStrategy = Callable[[ParentSelection], ReproduceFn]
