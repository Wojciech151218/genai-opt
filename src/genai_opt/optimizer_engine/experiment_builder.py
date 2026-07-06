from __future__ import annotations

from typing import Generic

from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import (
    ReproductionPolicy,
)
from genai_opt.optimizer_engine.utils.types import Types as T
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class ExperimentBuilder(Generic[P, Inv]):
    def __init__(
        self,
        inital_population_strategy: T.InitialPopulationStrategy,
        convergence_criterion: T.ConvergenceCriterion,
        mutation_policy: T.MutationPolicy,
        reproduction_policy: ReproductionPolicy,
        metrics_collector: T.MetricsCollector,
    ):
        self.inital_population_strategy = inital_population_strategy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy
        self.reproduction_policy = reproduction_policy
        self.metrics_collector = metrics_collector

    def build(self) -> Engine[P, Inv]:
        return Engine(
            self.inital_population_strategy(),
            self.convergence_criterion,
            self.mutation_policy,
            self.reproduction_policy,
            self.metrics_collector,
        )
