from __future__ import annotations

import asyncio

from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.utils.types import Types as T


class ReproductionPolicy:
    def __init__(
        self,
        reproduction_strategy: T.ReproductionStrategy,
        parent_selection: T.ParentSelection,
    ) -> None:
        self.reproduce = reproduction_strategy(parent_selection)

    async def get_new_population(self, population: T.Population) -> tuple[T.Population, list[Operation]]:
        result = self.reproduce(population)
        if asyncio.iscoroutine(result):
            return await result
        return result
