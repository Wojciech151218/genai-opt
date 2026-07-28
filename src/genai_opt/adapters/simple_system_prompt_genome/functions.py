"""Factories for the four operations a system-prompt genome needs.

Each function here returns the callable that
:class:`~genai_opt.adapters.simple_system_prompt_genome.genome.SimpleSystemPromptGenome`
expects, so an experiment is assembled from these rather than written as a
subclass. Every returned callable that talks to a model reports its token usage
and duration on the resulting
:class:`~genai_opt.optimizer_engine.operation.Operation`.
"""

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
    """Build a mutation that swaps the model and keeps the prompt.

    Useful for evolving which model serves a prompt. It makes no model call, so
    it is free.

    Args:
        llm_with_probabilities: Candidate models mapped to selection
            probabilities, which must sum to 1.

    Returns:
        A mutation function for the genome.

    Raises:
        ValueError: If the mapping is empty or its probabilities do not sum to 1.
    """
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
    """Build a mutation that asks an LLM to rewrite the system prompt.

    Args:
        prompt_message_str: Instruction template for the rewrite. Must contain a
            ``{system_prompt}`` placeholder, where the current prompt is
            substituted.
        llm: Model performing the rewrite, which need not be the one being
            optimized.

    Returns:
        A mutation function for the genome. Each call costs one model call.
    """

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
    """Build a crossover that asks an LLM to blend two system prompts.

    Args:
        prompt_message_str: Instruction template for the blend. Must contain
            ``{prompt_a}`` and ``{prompt_b}`` placeholders.
        llm: Model performing the blend.

    Returns:
        A crossover function for the genome. The child keeps the first parent's
        model. Each call costs one model call.
    """

    def crossover(
        self_phenotype: SimpleSystemPromptPhenotype,
        other_phenotype: SimpleSystemPromptPhenotype,
    ) -> Operation[SimpleSystemPromptPhenotype]:
        prompt = ensure_prompt_template(prompt_message_str)
        structured_llm = llm.with_structured_output(SystemPromptMutation, include_raw=True)
        start = time.perf_counter()
        result = (prompt | structured_llm).invoke(
            {
                "prompt_a": render_system_prompt(self_phenotype.system_prompt),
                "prompt_b": render_system_prompt(other_phenotype.system_prompt),
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
    """Build an evaluation that has an LLM judge the invocation output.

    Args:
        prompt_message_str: Judging instructions. Must contain an ``{output}``
            placeholder, where the invocation is substituted as JSON.
        llm: Model acting as the judge.
        evaluation_schema: Reply schema. Must define a float ``score`` field;
            extra fields are allowed and are useful for asking the judge to
            explain itself.

    Returns:
        An async evaluation function for the genome. Each call costs one model
        call.
    """

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
    """Build an invocation that sends one fixed task under the evolving prompt.

    Sharing a single task message across a population is what makes the
    comparison fair: the prompt is the only thing that differs.

    Args:
        task_message: The task every genome is asked to perform.
        invocation_schema: Pydantic model the reply is parsed into.

    Returns:
        An async invocation function for the genome. Each call costs one model
        call.
    """

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
    """Build a mutation that tries several strategies until one succeeds.

    Each candidate is tried in order and any exception moves on to the next, so
    order them best-first with a cheap or offline strategy last. This is how a
    run survives a flaky provider or a reply that will not parse.

    Args:
        mutate_functions: Strategies to try, in order of preference.

    Returns:
        A mutation function for the genome, which raises ``ValueError`` if every
        strategy fails.

    Raises:
        ValueError: If ``mutate_functions`` is empty.
    """
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
