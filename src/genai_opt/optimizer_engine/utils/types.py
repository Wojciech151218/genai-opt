from __future__ import annotations

from collections.abc import Awaitable, Callable

from genai_opt.optimizer_engine.genome import Genome as Gen
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector as MC,
)
from genai_opt.optimizer_engine.population import Population as Pop
from genai_opt.optimizer_engine.utils.typevars import I, P


class Types:
    type Genome = Gen[P, I]
    type Population = Pop[P, I]
    type Phenotype = P
    type GenomeAndFitness = tuple[Genome, float]
    type ConvergenceCriterion = Callable[[Population, int], bool]
    type InitialPopulationStrategy = Callable[[], Population]
    type MetricsCollector = MC[P, I]
    type MutationPolicy = Callable[[Genome], bool]
    type ParentPair = tuple[Genome, Genome]
    type ParentSelection = Callable[[Population], ParentPair]
    type ReproduceFn = Callable[[Population], Population | Awaitable[Population]]
    type ReproductionStrategy = Callable[[ParentSelection], ReproduceFn]
