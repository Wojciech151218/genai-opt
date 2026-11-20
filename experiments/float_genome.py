"""A minimal genome used by the credential-free example experiment."""

from __future__ import annotations

from random import uniform
from typing import Any, Self

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation


class FloatGenome(Genome):
    """Optimizes a single float toward a target value.

    The simplest possible genome, and the reference for what a genome must
    provide. Invocation just returns the phenotype, and fitness is
    ``100.0 - abs(value - target)``, so it peaks at 100 on the target. Nothing
    here needs credentials or network access, which makes it the genome to reach
    for when testing engine behavior.

    Args:
        phenotype: The starting value.
        target: The value being optimized toward.
        mutation_scale: Half-width of the uniform range a mutation draws from.
    """

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
        """Serialize the value along with its target and mutation scale."""
        return {
            **super().to_json(),
            "target": self.target,
            "mutation_scale": self.mutation_scale,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        """Rebuild a genome from a checkpoint payload.

        Args:
            data: The stored payload.
            **context: Optional ``target`` and ``mutation_scale`` fallbacks, used
                only when the payload predates those fields.

        Returns:
            The restored genome, including any stored fitness.

        Raises:
            ValueError: If the payload has no phenotype.
        """
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
        """Return the value unchanged; there is nothing to run."""
        return Operation(self.phenotype)

    async def evaluate(self) -> Operation[float]:
        """Score the value by its distance from the target, peaking at 100."""
        return Operation(100.0 - abs(self.invocation - self.target))

    async def mutate(self) -> Operation[Self]:
        """Return a child offset by a uniform random step."""
        delta = uniform(-self.mutation_scale, self.mutation_scale)
        child = FloatGenome(
            self.phenotype + delta,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )
        return Operation(child)

    async def crossover(self, other: Genome) -> Operation[Self]:
        """Return a child at the midpoint of the two parents' values."""
        child_value = (self.phenotype + other.phenotype) / 2
        child = FloatGenome(
            child_value,
            target=self.target,
            mutation_scale=self.mutation_scale,
        )
        return Operation(child)
