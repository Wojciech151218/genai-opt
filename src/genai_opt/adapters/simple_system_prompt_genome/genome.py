from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Generic, Self

from genai_opt.adapters.simple_system_prompt_genome.types import (
    InvSchema,
    SimpleSystemPromptPhenotype,
)
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation


class SimpleSystemPromptGenome(Genome[SimpleSystemPromptPhenotype, InvSchema], Generic[InvSchema]):
    def __init__(
        self,
        phenotype: SimpleSystemPromptPhenotype,
        *,
        invocation_schema: type[InvSchema],
        invoke_function: Callable[[SimpleSystemPromptPhenotype], Awaitable[Operation[InvSchema]]],
        evaluate_function: Callable[[InvSchema], Awaitable[Operation[float]]],
        mutate_function: Callable[[SimpleSystemPromptPhenotype], Operation[SimpleSystemPromptPhenotype]],
        crossover_function: Callable[
            [SimpleSystemPromptPhenotype, SimpleSystemPromptPhenotype],
            Operation[SimpleSystemPromptPhenotype],
        ],
    ):
        super().__init__(phenotype=phenotype)
        self._invocation_schema = invocation_schema
        self._invoke_function = invoke_function
        self._evaluate_function = evaluate_function
        self._mutate_function = mutate_function
        self._crossover_function = crossover_function

    def _child(self, phenotype: SimpleSystemPromptPhenotype) -> Self:
        return self.__class__(
            phenotype=phenotype,
            invocation_schema=self._invocation_schema,
            invoke_function=self._invoke_function,
            evaluate_function=self._evaluate_function,
            mutate_function=self._mutate_function,
            crossover_function=self._crossover_function,
        )

    def _child_operation(self, operation: Operation[SimpleSystemPromptPhenotype]) -> Operation[Self]:
        """Turn a phenotype operation into a genome operation, keeping id and metadata."""
        return Operation(
            self._child(operation.value),
            kind=operation.kind,
            duration_seconds=operation.duration_seconds,
            llm_metadata=operation.llm_metadata,
            id=operation.id,
        )

    async def invoke(self) -> Operation[InvSchema]:
        return await self._invoke_function(self.phenotype)

    async def evaluate(self) -> Operation[float]:
        return await self._evaluate_function(self.invocation)

    async def mutate(self) -> Operation[Self]:
        return self._child_operation(self._mutate_function(self.phenotype))

    async def crossover(self, other: Self) -> Operation[Self]:
        return self._child_operation(self._crossover_function(self.phenotype, other.phenotype))
