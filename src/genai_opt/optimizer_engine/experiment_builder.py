from __future__ import annotations

from typing import Generic

from genai_opt.optimizer_engine.checkpointer import Checkpointer, NullCheckpointer
from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.experiment_controller import ExperimentController, NullExperimentController
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
        checkpointer: Checkpointer[P, Inv] | None = None,
        experiment_controller: ExperimentController | None = None,
    ):
        self.inital_population_strategy = inital_population_strategy
        self.convergence_criterion = convergence_criterion
        self.mutation_policy = mutation_policy
        self.reproduction_policy = reproduction_policy
        self.checkpointer = checkpointer or NullCheckpointer()
        self.experiment_controller = experiment_controller or NullExperimentController()

    def build(self) -> Engine[P, Inv]:
        return Engine(
            self.inital_population_strategy(),
            self.convergence_criterion,
            self.mutation_policy,
            self.reproduction_policy,
            self.checkpointer,
            self.experiment_controller,
        )
