"""Pairing of a reproduction strategy with a parent selection strategy."""

from __future__ import annotations

import asyncio

from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.utils.types import Types as T


class ReproductionPolicy:
    """Produces each new generation from the current one.

    Splitting the two halves apart means "how many children and from what" is
    chosen independently of "which parents", so the strategies compose freely::

        ReproductionPolicy(generational_reproduction(20), tournament_selection)

    Args:
        reproduction_strategy: Decides how children are produced, for example
            :func:`~genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy.generational_reproduction`.
        parent_selection: Chooses the parents for each child, for example
            :func:`~genai_opt.optimizer_engine.reproduction_policy.parent_selection.tournament_selection`.
    """

    def __init__(
        self,
        reproduction_strategy: T.ReproductionStrategy,
        parent_selection: T.ParentSelection,
    ) -> None:
        self.reproduce = reproduction_strategy(parent_selection)

    async def get_new_population(self, population: T.Population) -> tuple[T.Population, list[Operation]]:
        """Build the offspring generation.

        Accepts both synchronous and asynchronous reproduction functions, so a
        custom strategy need not be a coroutine when it does no I/O.

        Args:
            population: The evaluated current generation.

        Returns:
            The offspring population and the operations that created it, the
            latter carrying the LLM cost and token usage of any model calls.
        """
        result = self.reproduce(population)
        if asyncio.iscoroutine(result):
            return await result
        return result
