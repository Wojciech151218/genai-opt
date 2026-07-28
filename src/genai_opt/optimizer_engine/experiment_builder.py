"""Assembly of a configured engine from its policies and strategies."""

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
    """Collects an experiment's configuration and builds the engine from it.

    The difference from constructing an :class:`~genai_opt.optimizer_engine.engine.Engine`
    directly is that the initial population is described as a strategy rather
    than passed in, so nothing is created until :meth:`build` is called. That
    matters when generation zero is expensive, and it lets one builder produce
    several independent runs.

    Args:
        inital_population_strategy: Called by :meth:`build` to create generation
            zero.
        convergence_criterion: Decides when to stop iterating.
        mutation_policy: Decides, per offspring genome, whether to mutate it.
        reproduction_policy: Produces each offspring generation.
        checkpointer: Persists state after every phase. Defaults to keeping
            nothing.
        experiment_controller: Observes phases and operations, and can pause the
            run. Defaults to reporting nothing.
    """

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
        """Create generation zero and return an engine configured to run it.

        Chain :meth:`~genai_opt.optimizer_engine.engine.Engine.from_checkpoint`
        onto the result to resume a previous run where it left off.

        Returns:
            A ready-to-run engine.
        """
        return Engine(
            self.inital_population_strategy(),
            self.convergence_criterion,
            self.mutation_policy,
            self.reproduction_policy,
            self.checkpointer,
            self.experiment_controller,
        )
