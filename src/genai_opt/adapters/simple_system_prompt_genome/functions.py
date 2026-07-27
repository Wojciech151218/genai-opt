from __future__ import annotations

import random
from collections.abc import Awaitable, Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from pydantic import BaseModel

from genai_opt.adapters.simple_system_prompt_genome.helpers import (
    build_invoke_chat_prompt,
    ensure_prompt_template,
    extract_score,
    format_invocation_for_evaluation,
    render_system_prompt,
)
from genai_opt.adapters.simple_system_prompt_genome.types import (
    EvaluationScore,
    InvSchema,
    SimpleSystemPromptPhenotype,
    SystemPromptMutation,
)


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
        prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(prompt_message_str)])
        structured_llm = llm.with_structured_output(SystemPromptMutation)
        result = (prompt | structured_llm).invoke({"system_prompt": render_system_prompt(phenotype.system_prompt)})
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
        prompt = ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(SystemPromptMutation)
        result = (prompt | structured_llm).invoke(
            {
                "prompt_a": render_system_prompt(self_phenotype.system_prompt),
                "prompt_b": render_system_prompt(other_phenotype.system_prompt),
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
        prompt = ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(evaluation_schema)
        chain = prompt | structured_llm
        result = await chain.ainvoke({"output": format_invocation_for_evaluation(invocation)})
        return extract_score(result)

    return evaluate


def invoke_task_message_function(
    task_message: BaseMessage,
    invocation_schema: type[InvSchema],
) -> Callable[[SimpleSystemPromptPhenotype], Awaitable[InvSchema]]:
    async def invoke(phenotype: SimpleSystemPromptPhenotype) -> InvSchema:
        prompt = build_invoke_chat_prompt(phenotype.system_prompt)
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
