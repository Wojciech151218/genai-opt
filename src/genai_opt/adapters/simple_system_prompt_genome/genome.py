from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Generic, Self

from genai_opt.adapters.simple_system_prompt_genome.helpers import (
    llm_from_config,
    llm_to_config,
    render_system_prompt,
)
from genai_opt.adapters.simple_system_prompt_genome.types import (
    InvSchema,
    SimpleSystemPromptPhenotype,
)
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.serialization import deserialize_value, import_type, type_path


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

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "system_prompt": render_system_prompt(self.phenotype.system_prompt),
            "llm_config": llm_to_config(self.phenotype.llm),
            "invocation_schema": type_path(self._invocation_schema),
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        invocation_schema = context.get("invocation_schema")
        if invocation_schema is None:
            schema_path = data.get("invocation_schema")
            if schema_path is None:
                raise ValueError("invocation_schema is required in context or checkpoint data")
            invocation_schema = import_type(schema_path)

        invoke_function = context.get("invoke_function")
        evaluate_function = context.get("evaluate_function")
        mutate_function = context.get("mutate_function")
        crossover_function = context.get("crossover_function")
        missing = [
            name
            for name, value in (
                ("invoke_function", invoke_function),
                ("evaluate_function", evaluate_function),
                ("mutate_function", mutate_function),
                ("crossover_function", crossover_function),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"Missing restore context for SimpleSystemPromptGenome: {', '.join(missing)}")

        llm = context.get("llm")
        if llm is None:
            llm_config = data.get("llm_config")
            if llm_config is None:
                raise ValueError("llm or llm_config is required to restore SimpleSystemPromptGenome")
            llm = llm_from_config(llm_config, api_key=context.get("api_key"))

        system_prompt = data.get("system_prompt")
        if system_prompt is None and data.get("phenotype") is not None:
            phenotype_data = data["phenotype"]
            if isinstance(phenotype_data, dict):
                system_prompt = phenotype_data.get("system_prompt")

        if system_prompt is None:
            raise ValueError("system_prompt is required to restore SimpleSystemPromptGenome")

        genome = cls(
            phenotype=SimpleSystemPromptPhenotype(system_prompt=system_prompt, llm=llm),
            invocation_schema=invocation_schema,
            invoke_function=invoke_function,
            evaluate_function=evaluate_function,
            mutate_function=mutate_function,
            crossover_function=crossover_function,
        )
        genome._restore_runtime_state(data, invocation_schema=invocation_schema)
        return genome

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
