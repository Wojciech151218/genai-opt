from __future__ import annotations

from genai_opt.optimizer_engine.utils.types import Types as T


def iteration_limited_convergence(
    iteration_limit: int,
) -> T.ConvergenceCriterion:
    def is_converged(population: T.Population, iteration: int) -> bool:
        return iteration >= iteration_limit

    return is_converged
