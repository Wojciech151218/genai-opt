from __future__ import annotations

from typing import Callable, TypeVar

from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector,
)
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import (
    ReproductionPolicy,
)

INVOCATION = TypeVar("INVOCATION")
PHENOTYPE = TypeVar("PHENOTYPE")


class ExperimentBuilder:
    def __init__(
        self,
        inital_population_strategy: Callable[[], Population[PHENOTYPE, INVOCATION]],
        convergence_criterion: Callable[
            [Population[PHENOTYPE, INVOCATION], int], bool
        ],
        mutation_policy: Callable[[Genome[PHENOTYPE, INVOCATION]], bool],
        reproduction_policy: ReproductionPolicy,
        metrics_collector: MetricsCollector,
    ):
        self.inital_population_strategy = inital_population_strategy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy
        self.reproduction_policy = reproduction_policy
        self.metrics_collector = metrics_collector

    def build(self) -> Engine:
        return Engine(
            self.inital_population_strategy(),
            self.convergence_criterion,
            self.mutation_policy,
            self.reproduction_policy,
            self.metrics_collector,
        )
