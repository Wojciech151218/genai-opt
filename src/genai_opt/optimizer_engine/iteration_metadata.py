"""Statistics reported for one phase of one iteration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.utils.typevars import Inv, P

if TYPE_CHECKING:
    from genai_opt.optimizer_engine.population import Population


@dataclass
class PhenotypeState(Generic[P, Inv]):
    """A snapshot of one genome, without the genome's behavior.

    Attributes:
        phenotype: The representation being optimized.
        fitness: The genome's score, or ``None`` if it was not evaluated yet.
        invocation: The invocation output, or ``None`` if it was not invoked yet.
    """

    phenotype: P
    fitness: float | None = None
    invocation: Inv | None = None


@dataclass
class IterationMetadata(Generic[P, Inv]):
    """What happened during one phase: the population snapshot and its operations.

    Returned by ``Engine.step()`` and handed to experiment controllers and
    checkpointers. The cost and token totals come from the operations, so they
    cover only the model calls made in this phase.

    Attributes:
        iteration: The iteration this phase belongs to.
        phase: Which phase ran, or ``None`` when not attributed to one.
        phenotype_states: A snapshot of the population the phase touched.
        operations: Operations performed during the phase.
    """

    iteration: int
    phase: IterationPhase | None = None
    phenotype_states: list[PhenotypeState[P, Inv]] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        """Tokens used by this phase's model calls."""
        return sum(operation.tokens for operation in self.operations)

    @property
    def total_cost(self) -> float:
        """Cost of this phase, counting only operations that reported one."""
        return sum(operation.cost for operation in self.operations)

    @property
    def total_duration_seconds(self) -> float:
        """Summed operation durations.

        Operations run concurrently, so this exceeds the phase's wall-clock time.
        """
        return sum(operation.duration_seconds for operation in self.operations)

    def tokens_by_kind(self, kind: OperationKind) -> int:
        """Tokens used by operations of one kind, such as ``"evaluate"``."""
        return sum(operation.tokens for operation in self.operations if operation.kind == kind)

    def duration_by_kind(self, kind: OperationKind) -> float:
        """Summed duration of operations of one kind, such as ``"mutation"``."""
        return sum(operation.duration_seconds for operation in self.operations if operation.kind == kind)

    @classmethod
    def from_population(
        cls,
        iteration: int,
        population: Population[P, Inv],
        operations: list[Operation],
        phase: IterationPhase | None = None,
    ) -> IterationMetadata[P, Inv]:
        """Snapshot a population into metadata.

        Genomes that have not been invoked or evaluated yet are recorded with
        ``None`` rather than raising, so a phase can be reported mid-iteration.

        Args:
            iteration: The current iteration number.
            population: The population to snapshot.
            operations: Operations performed during the phase.
            phase: Which phase this describes.

        Returns:
            The assembled metadata.
        """
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
            phase=phase,
            phenotype_states=phenotype_states,
            operations=operations,
        )
