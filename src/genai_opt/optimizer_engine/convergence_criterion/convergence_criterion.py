from __future__ import annotations

from typing import Callable, TypeVar

from genai_opt.optimizer_engine.population import Population

INVOCATION = TypeVar("INVOCATION")
PHENOTYPE = TypeVar("PHENOTYPE")


def convergence_function(
    iteration_limit: int,
) -> Callable[[Population[PHENOTYPE, INVOCATION], int], bool]:
    def is_converged(
        population: Population[PHENOTYPE, INVOCATION], iteration: int
    ) -> bool:
        return iteration >= iteration_limit

    return is_converged
