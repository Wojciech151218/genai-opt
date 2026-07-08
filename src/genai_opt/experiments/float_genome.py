from __future__ import annotations

from random import uniform
from typing import Self

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation


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

    async def invoke(self) -> Operation[float]:
        return Operation(self.phenotype)

    async def evaluate(self) -> Operation[float]:
        return Operation(100.0 - abs(self.invocation - self.target))

    async def mutate(self) -> Operation[Self]:
        delta = uniform(-self.mutation_scale, self.mutation_scale)
        child = FloatGenome(
            self.phenotype + delta,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )
        return Operation(child)

    async def crossover(self, other: Genome) -> Operation[Self]:
        child_value = (self.phenotype + other.phenotype) / 2
        child = FloatGenome(
            child_value,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )
        return Operation(child)
