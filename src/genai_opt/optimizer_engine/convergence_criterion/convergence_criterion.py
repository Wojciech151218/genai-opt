"""Criteria deciding when a run is finished."""

from __future__ import annotations

from genai_opt.optimizer_engine.utils.types import Types as T


def iteration_limited_convergence(
    iteration_limit: int,
) -> T.ConvergenceCriterion:
    """Stop after a fixed number of iterations, whatever the fitness.

    A predictable budget, which is what you usually want for LLM-backed runs.
    The limit is also the natural way to bound spend, since each iteration costs
    roughly the same number of model calls.

    Args:
        iteration_limit: Iterations to run. ``0`` returns the initial population
            evaluated but otherwise untouched.

    Returns:
        A criterion the engine checks at the top of each iteration.
    """

    def is_converged(population: T.Population, iteration: int) -> bool:
        return iteration >= iteration_limit

    return is_converged
