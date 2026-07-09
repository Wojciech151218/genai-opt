from __future__ import annotations

import random
import time
from collections.abc import Awaitable, Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from pydantic import BaseModel

from genai_opt.adapters.simple_system_prompt_genome.helpers import (
    build_invoke_chat_prompt,
    build_operation,
    ensure_prompt_template,
    extract_parsed,
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
from genai_opt.optimizer_engine.operation import Operation


def llm_mutate_function(
    llm_with_probabilities: dict[BaseChatModel, float],
) -> Callable[[SimpleSystemPromptPhenotype], Operation[SimpleSystemPromptPhenotype]]:
    if not llm_with_probabilities:
        raise ValueError("llm_with_probabilities must not be empty")
    if abs(sum(llm_with_probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("llm_with_probabilities must sum to 1")

    def mutate(phenotype: SimpleSystemPromptPhenotype) -> Operation[SimpleSystemPromptPhenotype]:
        llm = random.choices(
            list(llm_with_probabilities.keys()),
            weights=list(llm_with_probabilities.values()),
        )[0]
        return Operation(
            SimpleSystemPromptPhenotype(
                system_prompt=phenotype.system_prompt,
                llm=llm,
            )
        )

    return mutate


def mutate_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
) -> Callable[[SimpleSystemPromptPhenotype], Operation[SimpleSystemPromptPhenotype]]:
    def mutate(phenotype: SimpleSystemPromptPhenotype) -> Operation[SimpleSystemPromptPhenotype]:
        prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(prompt_message_str)])
        structured_llm = llm.with_structured_output(SystemPromptMutation, include_raw=True)
        start = time.perf_counter()
        result = (prompt | structured_llm).invoke({"system_prompt": render_system_prompt(phenotype.system_prompt)})
        elapsed = time.perf_counter() - start
        mutation = extract_parsed(result)
        return build_operation(
            SimpleSystemPromptPhenotype(
                system_prompt=mutation.system_prompt,
                llm=phenotype.llm,
            ),
            result,
            time_seconds=elapsed,
        )

    return mutate


def crossover_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
) -> Callable[
    [SimpleSystemPromptPhenotype, SimpleSystemPromptPhenotype],
    Operation[SimpleSystemPromptPhenotype],
]:
    def crossover(
        self_phenotype: SimpleSystemPromptPhenotype,
        other_phenotype: SimpleSystemPromptPhenotype,
    ) -> Operation[SimpleSystemPromptPhenotype]:
        prompt = ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(SystemPromptMutation, include_raw=True)
        start = time.perf_counter()
        result = (prompt | structured_llm).invoke(
            {
                "self": render_system_prompt(self_phenotype.system_prompt),
                "other": render_system_prompt(other_phenotype.system_prompt),
            }
        )
        elapsed = time.perf_counter() - start
        mutation = extract_parsed(result)
        return build_operation(
            SimpleSystemPromptPhenotype(
                system_prompt=mutation.system_prompt,
                llm=self_phenotype.llm,
            ),
            result,
            time_seconds=elapsed,
        )

    return crossover


def evaluate_prompt_function(
    prompt_message_str: str,
    llm: BaseChatModel,
    evaluation_schema: type[BaseModel] = EvaluationScore,
) -> Callable[[BaseModel], Awaitable[Operation[float]]]:
    async def evaluate(invocation: BaseModel) -> Operation[float]:
        prompt = ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(evaluation_schema, include_raw=True)
        chain = prompt | structured_llm
        start = time.perf_counter()
        result = await chain.ainvoke({"output": format_invocation_for_evaluation(invocation)})
        elapsed = time.perf_counter() - start
        return build_operation(
            extract_score(extract_parsed(result)),
            result,
            time_seconds=elapsed,
        )

    return evaluate


def invoke_task_message_function(
    task_message: BaseMessage,
    invocation_schema: type[InvSchema],
) -> Callable[[SimpleSystemPromptPhenotype], Awaitable[Operation[InvSchema]]]:
    async def invoke(phenotype: SimpleSystemPromptPhenotype) -> Operation[InvSchema]:
        prompt = build_invoke_chat_prompt(phenotype.system_prompt)
        structured_llm = phenotype.llm.with_structured_output(invocation_schema, include_raw=True)
        chain = prompt | structured_llm
        start = time.perf_counter()
        result = await chain.ainvoke({"task_messages": [task_message]})
        elapsed = time.perf_counter() - start
        return build_operation(extract_parsed(result), result, time_seconds=elapsed)

    return invoke


def mixed_mutate_function(
    mutate_functions: list[Callable[[SimpleSystemPromptPhenotype], Operation[SimpleSystemPromptPhenotype]]],
) -> Callable[[SimpleSystemPromptPhenotype], Operation[SimpleSystemPromptPhenotype]]:
    if len(mutate_functions) == 0:
        raise ValueError("mutate_functions must not be empty")

    def mutate(phenotype: SimpleSystemPromptPhenotype) -> Operation[SimpleSystemPromptPhenotype]:
        for mutate_function in mutate_functions:
            try:
                return mutate_function(phenotype)
            except Exception:
                continue
        raise ValueError("No mutate function succeeded")

    return mutate
