from __future__ import annotations

import random
from collections.abc import Awaitable, Callable
from typing import Generic, Self, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel, Field

from genai_opt.optimizer_engine.genome import Genome

SystemPrompt = str | PromptTemplate
InvSchema = TypeVar("InvSchema", bound=BaseModel)


class EvaluationScore(BaseModel):
    score: float = Field(description="Fitness score for the invocation output")


class SystemPromptMutation(BaseModel):
    system_prompt: str = Field(description="The evolved system prompt")


def _render_system_prompt(prompt: SystemPrompt) -> str:
    if isinstance(prompt, str):
        return prompt
    return prompt.format()


def _ensure_prompt_template(prompt: SystemPrompt) -> PromptTemplate:
    if isinstance(prompt, str):
        return PromptTemplate.from_template(prompt)
    return prompt


def _system_message_template(system_prompt: SystemPrompt) -> tuple[str, str] | SystemMessagePromptTemplate:
    if isinstance(system_prompt, str):
        return ("system", system_prompt)
    return SystemMessagePromptTemplate(prompt=system_prompt)


def _build_invoke_chat_prompt(system_prompt: SystemPrompt) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            _system_message_template(system_prompt),
            MessagesPlaceholder("task_messages"),
        ]
    )


def _format_invocation_for_evaluation(invocation: BaseModel) -> str:
    return invocation.model_dump_json()


def _extract_score(result: BaseModel) -> float:
    score = getattr(result, "score", None)
    if score is None:
        raise ValueError("evaluation_schema must define a 'score' field of type float")
    return float(score)


class SimpleSystemPromptPhenotype(BaseModel):
    system_prompt: SystemPrompt = Field(description="The system prompt")
    llm: BaseChatModel = Field(description="The LLM to use for the system prompt")


def llm_mutate_function(
    llm_with_probabilities: dict[BaseChatModel, float],
) -> Callable[[SimpleSystemPromptPhenotype], SimpleSystemPromptPhenotype]:
    if not llm_with_probabilities:
        raise ValueError("llm_with_probabilities must not be empty")
    if abs(sum(llm_with_probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("llm_with_probabilities must sum to 1")

    def mutate(phenotype: SimpleSystemPromptPhenotype) -> SimpleSystemPromptPhenotype:
        llm = random.choices(
            list(llm_with_probabilities.keys()),
            weights=list(llm_with_probabilities.values()),
        )[0]
        return SimpleSystemPromptPhenotype(
            system_prompt=phenotype.system_prompt,
            llm=llm,
        )

    return mutate


def mutate_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
) -> Callable[[SimpleSystemPromptPhenotype], SimpleSystemPromptPhenotype]:
    def mutate(phenotype: SimpleSystemPromptPhenotype) -> SimpleSystemPromptPhenotype:
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(prompt_message_str)]
        )
        structured_llm = llm.with_structured_output(SystemPromptMutation)
        result = (prompt | structured_llm).invoke(
            {"system_prompt": _render_system_prompt(phenotype.system_prompt)}
        )
        return SimpleSystemPromptPhenotype(
            system_prompt=result.system_prompt,
            llm=phenotype.llm,
        )

    return mutate


def crossover_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
) -> Callable[
    [SimpleSystemPromptPhenotype, SimpleSystemPromptPhenotype],
    SimpleSystemPromptPhenotype,
]:
    def crossover(
        self_phenotype: SimpleSystemPromptPhenotype,
        other_phenotype: SimpleSystemPromptPhenotype,
    ) -> SimpleSystemPromptPhenotype:
        prompt = _ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(SystemPromptMutation)
        result = (prompt | structured_llm).invoke(
            {
                "self": _render_system_prompt(self_phenotype.system_prompt),
                "other": _render_system_prompt(other_phenotype.system_prompt),
            }
        )
        return SimpleSystemPromptPhenotype(
            system_prompt=result.system_prompt,
            llm=self_phenotype.llm,
        )

    return crossover


def evaluate_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
    evaluation_schema: type[BaseModel] = EvaluationScore,
) -> Callable[[BaseModel], Awaitable[float]]:
    async def evaluate(invocation: BaseModel) -> float:
        prompt = _ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(evaluation_schema)
        chain = prompt | structured_llm
        result = await chain.ainvoke(
            {"output": _format_invocation_for_evaluation(invocation)}
        )
        return _extract_score(result)

    return evaluate


def invoke_task_message_function(
    task_message: BaseMessage,
    invocation_schema: type[InvSchema],
) -> Callable[[SimpleSystemPromptPhenotype], Awaitable[InvSchema]]:
    async def invoke(phenotype: SimpleSystemPromptPhenotype) -> InvSchema:
        prompt = _build_invoke_chat_prompt(phenotype.system_prompt)
        structured_llm = phenotype.llm.with_structured_output(invocation_schema)
        chain = prompt | structured_llm
        return await chain.ainvoke({"task_messages": [task_message]})

    return invoke


def mixed_mutate_function(
    mutate_functions: list[Callable[[SimpleSystemPromptPhenotype], SimpleSystemPromptPhenotype]],
) -> Callable[[SimpleSystemPromptPhenotype], SimpleSystemPromptPhenotype]:
    if len(mutate_functions) == 0:
        raise ValueError("mutate_functions must not be empty")

    def mutate(phenotype: SimpleSystemPromptPhenotype) -> SimpleSystemPromptPhenotype:
        for mutate_function in mutate_functions:
            try:
                return mutate_function(phenotype)
            except Exception:
                continue
        raise ValueError("No mutate function succeeded")

    return mutate


class SimpleSystemPromptGenome(Genome[SimpleSystemPromptPhenotype, InvSchema], Generic[InvSchema]):
    def __init__(
        self,
        phenotype: SimpleSystemPromptPhenotype,
        *,
        invocation_schema: type[InvSchema],
        invoke_function: Callable[[SimpleSystemPromptPhenotype], Awaitable[InvSchema]],
        evaluate_function: Callable[[InvSchema], Awaitable[float]],
        mutate_function: Callable[[SimpleSystemPromptPhenotype], SimpleSystemPromptPhenotype],
        crossover_function: Callable[
            [SimpleSystemPromptPhenotype, SimpleSystemPromptPhenotype],
            SimpleSystemPromptPhenotype,
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

    async def invoke(self) -> InvSchema:
        return await self._invoke_function(self.phenotype)

    async def evaluate(self) -> float:
        return await self._evaluate_function(self.invocation)

    async def mutate(self) -> Self:
        return self._child(self._mutate_function(self.phenotype))

    async def crossover(self, other: Self) -> Self:
        return self._child(self._crossover_function(self.phenotype, other.phenotype))
