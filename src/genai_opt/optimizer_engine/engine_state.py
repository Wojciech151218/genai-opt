"""The resumable state of a run, and the phases an iteration moves through."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic

from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class IterationPhase(StrEnum):
    """The five steps of one iteration, in the order the engine runs them.

    ``Engine.step()`` executes exactly one phase, which is what makes a run
    resumable at this granularity:

    1. ``EVALUATE_POPULATION`` - invoke and score the current generation.
    2. ``REPRODUCE`` - cross over selected parents into an offspring generation.
    3. ``MUTATE`` - apply the mutation policy to those offspring.
    4. ``EVALUATE_OFFSPRING`` - invoke and score the offspring.
    5. ``REPLACE`` - promote the offspring and increment the iteration counter.

    Values are stable strings, since they are written into checkpoints.
    """

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

    Attributes:
        population: The current generation.
        iteration: How many complete iterations have finished.
        phase: The next phase to execute.
        offspring_population: Candidate next generation, present only between
            the reproduce and replace phases.
        iteration_operations: Operations recorded so far in the current
            iteration, reset when a new one begins.
    """

    population: Population[P, Inv]
    iteration: int = 0
    phase: IterationPhase = IterationPhase.EVALUATE_POPULATION
    offspring_population: Population[P, Inv] | None = None
    iteration_operations: list[Operation] = field(default_factory=list)
