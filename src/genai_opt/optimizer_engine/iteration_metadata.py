from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic

from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.utils.typevars import Inv, P

if TYPE_CHECKING:
    from genai_opt.optimizer_engine.population import Population


@dataclass
class PhenotypeState(Generic[P, Inv]):
    phenotype: P
    fitness: float | None = None
    invocation: Inv | None = None


@dataclass
class IterationMetadata(Generic[P, Inv]):
    iteration: int
    phenotype_states: list[PhenotypeState[P, Inv]] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(operation.tokens for operation in self.operations)

    @property
    def total_cost(self) -> float:
        return sum(operation.cost for operation in self.operations)

    @property
    def total_duration_seconds(self) -> float:
        return sum(operation.duration_seconds for operation in self.operations)

    def tokens_by_kind(self, kind: OperationKind) -> int:
        return sum(operation.tokens for operation in self.operations if operation.kind == kind)

    def duration_by_kind(self, kind: OperationKind) -> float:
        return sum(operation.duration_seconds for operation in self.operations if operation.kind == kind)

    @classmethod
    def from_population(
        cls,
        iteration: int,
        population: Population[P, Inv],
        operations: list[Operation],
    ) -> IterationMetadata[P, Inv]:
        phenotype_states: list[PhenotypeState[P, Inv]] = []
        for genome in population.population:
            fitness: float | None = None
            invocation: Inv | None = None
            try:
                fitness = genome.evaluation
            except ValueError:
                pass
            try:
                invocation = genome.invocation
            except ValueError:
                pass
            phenotype_states.append(
                PhenotypeState(
                    phenotype=genome.phenotype,
                    fitness=fitness,
                    invocation=invocation,
                )
            )
        return cls(
            iteration=iteration,
            phenotype_states=phenotype_states,
            operations=operations,
        )
