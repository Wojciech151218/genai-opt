from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic

from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class IterationPhase(StrEnum):
    EVALUATE_POPULATION = "evaluate_population"
    REPRODUCE = "reproduce"
    MUTATE = "mutate"
    EVALUATE_OFFSPRING = "evaluate_offspring"
    REPLACE = "replace"


@dataclass
class EngineState(Generic[P, Inv]):
    """The complete, resumable state of an engine run.

    ``phase`` is always the *next* phase to execute. A checkpoint is therefore
    safe to resume directly without repeating a completed phase.
    """

    population: Population[P, Inv]
    iteration: int = 0
    phase: IterationPhase = IterationPhase.EVALUATE_POPULATION
    offspring_population: Population[P, Inv] | None = None
    iteration_operations: list[Operation] = field(default_factory=list)
