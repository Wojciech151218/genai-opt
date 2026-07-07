from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from genai_opt.optimizer_engine.genome import Genome as Gen
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector as MC,
)
from genai_opt.optimizer_engine.population import Population as Pop

P = TypeVar("PHENOTYPE")
Inv = TypeVar("INVOCATION")

type ParentPair[P, Inv] = tuple[Gen[P, Inv], Gen[P, Inv]]


class Types:
    type Genome = Gen[P, Inv]
    type Population = Pop[P, Inv]
    type ConvergenceCriterion = Callable[[Population[P, Inv], int], bool]
    type InitialPopulationStrategy = Callable[[Any, ...], Pop[P, Inv]]
    type MetricsCollector = MC[P, Inv]
    type MutationPolicy = Callable[[Gen[P, Inv]], bool]
    type ParentSelection = Callable[[Pop[P, Inv]], ParentPair[P, Inv]]
    type ReproduceFn = Callable[[Pop[P, Inv]], Pop[P, Inv] | Awaitable[Pop[P, Inv]]]
    type ReproductionStrategy = Callable[[ParentSelection], ReproduceFn]
