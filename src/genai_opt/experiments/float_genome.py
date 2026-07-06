from __future__ import annotations

from random import uniform
from typing import Self

from genai_opt.optimizer_engine.genome import Genome


class FloatGenome(Genome):
    """Optimizes a single float toward a target value."""

    def __init__(
        self,
        phenotype: float,
        target: float = 50.0,
        mutation_scale: float = 5.0,
    ):
        super().__init__(phenotype)
        self.target = target
        self.mutation_scale = mutation_scale

    async def invoke(self) -> float:
        return self.phenotype

    async def evaluate(self) -> float:
        return 100.0 - abs(self.invocation - self.target)

    async def mutate(self) -> Self:
        delta = uniform(-self.mutation_scale, self.mutation_scale)
        return FloatGenome(
            self.phenotype + delta,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )

    async def crossover(self, other: Genome) -> Self:
        child_value = (self.phenotype + other.phenotype) / 2
        return FloatGenome(
            child_value,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )

    x = 5
