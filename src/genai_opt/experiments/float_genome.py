from __future__ import annotations

from random import uniform
from typing import Any, Self

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

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "target": self.target,
            "mutation_scale": self.mutation_scale,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        phenotype = data.get("phenotype")
        if phenotype is None:
            raise ValueError("FloatGenome checkpoint data must include phenotype")

        genome = cls(
            float(phenotype),
            target=float(data.get("target", context.get("target", 50.0))),
            mutation_scale=float(data.get("mutation_scale", context.get("mutation_scale", 5.0))),
        )
        genome._restore_runtime_state(data)
        return genome

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
