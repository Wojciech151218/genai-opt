from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from genai_opt.optimizer_engine.population import Population

ReproduceFn = Callable[
    [Population],
    Population | Awaitable[Population],
]


class ReproductionPolicy:
    def __init__(self, reproduce: ReproduceFn) -> None:
        self.reproduce = reproduce

    async def get_new_population(self, population: Population) -> Population:
        result = self.reproduce(population)
        if asyncio.iscoroutine(result):
            return await result
        return result
