"""Tests for the simple_system_prompt_genome adapter functions and LLM metadata plumbing."""

import asyncio

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from genai_opt.adapters.simple_system_prompt_genome.functions import (
    evaluate_prompt_function,
    invoke_task_message_function,
    llm_mutate_function,
    mutate_prompt_function,
)
from genai_opt.adapters.simple_system_prompt_genome.genome import SimpleSystemPromptGenome
from genai_opt.adapters.simple_system_prompt_genome.helpers import (
    build_operation,
    extract_parsed,
)
from genai_opt.adapters.simple_system_prompt_genome.types import (
    EvaluationScore,
    SimpleSystemPromptPhenotype,
)
from genai_opt.optimizer_engine.operation import Operation

_USAGE = {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20}
_RESPONSE_METADATA = {"model_name": "fake-model"}


class _FakeStructuredModel(BaseChatModel):
    """Chat model whose structured output chain returns a canned include_raw dict."""

    # llm_mutate_function keys a dict by chat model; pydantic models are unhashable by default
    __hash__ = object.__hash__

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError

    def with_structured_output(self, schema, **kwargs):
        def respond(_input):
            if schema is EvaluationScore or "score" in schema.model_fields:
                parsed = schema(score=88.0)
            else:
                parsed = schema(system_prompt="evolved prompt")
            return {
                "raw": AIMessage(
                    content="",
                    usage_metadata=_USAGE,
                    response_metadata=_RESPONSE_METADATA,
                ),
                "parsed": parsed,
                "parsing_error": None,
            }

        return RunnableLambda(respond)


def _phenotype() -> SimpleSystemPromptPhenotype:
    return SimpleSystemPromptPhenotype(
        system_prompt="You are a poet.",
        llm=_FakeStructuredModel(),
    )


def test_extract_parsed_unwraps_include_raw_dict():
    assert extract_parsed({"raw": None, "parsed": 42, "parsing_error": None}) == 42


def test_extract_parsed_raises_parsing_error():
    with pytest.raises(RuntimeError, match="bad output"):
        extract_parsed({"raw": None, "parsed": None, "parsing_error": RuntimeError("bad output")})


def test_extract_parsed_passes_through_plain_value():
    assert extract_parsed("plain") == "plain"


def test_build_operation_attaches_llm_metadata():
    raw = AIMessage(content="", usage_metadata=_USAGE, response_metadata=_RESPONSE_METADATA)
    operation = build_operation("value", {"raw": raw, "parsed": "value"}, time_seconds=0.5)
    assert operation.llm_metadata is not None
    assert operation.llm_metadata.model == "fake-model"
    assert operation.tokens == 20
    assert operation.llm_metadata.time_seconds == 0.5


def test_build_operation_falls_back_without_usage():
    raw = AIMessage(content="no usage here")
    operation = build_operation("value", {"raw": raw, "parsed": "value"})
    assert operation.llm_metadata is None
    assert operation.value == "value"


def test_mutate_prompt_function_returns_operation_with_metadata():
    mutate = mutate_prompt_function("Improve: {system_prompt}", _FakeStructuredModel())
    operation = mutate(_phenotype())
    assert isinstance(operation, Operation)
    assert operation.value.system_prompt == "evolved prompt"
    assert operation.tokens == 20
    assert operation.llm_metadata.model == "fake-model"


def test_evaluate_prompt_function_returns_operation_with_metadata():
    evaluate = evaluate_prompt_function("Judge: {output}", _FakeStructuredModel())
    operation = asyncio.run(evaluate(EvaluationScore(score=0.0)))
    assert operation.value == 88.0
    assert operation.tokens == 20


def test_llm_mutate_function_returns_bare_operation():
    llm = _FakeStructuredModel()
    mutate = llm_mutate_function({llm: 1.0})
    operation = mutate(_phenotype())
    assert isinstance(operation, Operation)
    assert operation.llm_metadata is None
    assert operation.value.llm is llm


def test_genome_mutate_preserves_metadata_and_id():
    from langchain_core.messages import HumanMessage

    genome = SimpleSystemPromptGenome(
        phenotype=_phenotype(),
        invocation_schema=EvaluationScore,
        invoke_function=invoke_task_message_function(HumanMessage(content="go"), EvaluationScore),
        evaluate_function=evaluate_prompt_function("Judge: {output}", _FakeStructuredModel()),
        mutate_function=mutate_prompt_function("Improve: {system_prompt}", _FakeStructuredModel()),
        crossover_function=lambda a, b: Operation(a),
    )
    operation = asyncio.run(genome._mutate())

    assert operation.kind == "mutation"
    assert isinstance(operation.value, SimpleSystemPromptGenome)
    assert operation.value.phenotype.system_prompt == "evolved prompt"
    assert operation.tokens == 20
