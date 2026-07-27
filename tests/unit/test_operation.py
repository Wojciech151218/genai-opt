"""Tests for Operation and LLMMetadata."""

import pytest
from langchain_core.messages import AIMessage

from genai_opt.optimizer_engine.operation import LLMMetadata, Operation


def test_operation_defaults():
    operation = Operation("some value")
    assert operation.kind == "unknown"
    assert operation.value == "some value"
    assert operation.duration_seconds == 0.0
    assert operation.llm_metadata is None
    assert operation.tokens == 0
    assert operation.cost == 0.0


def test_operation_random_uuid_is_unique():
    assert Operation(1).id != Operation(1).id


def test_operation_elastic_constructor_builds_llm_metadata():
    operation = Operation(
        "value",
        kind="invoke",
        model="gpt-4o-mini",
        cost=0.002,
        time_seconds=1.5,
        tokens_in=100,
        tokens_out=50,
    )
    assert operation.llm_metadata is not None
    assert operation.llm_metadata.model == "gpt-4o-mini"
    assert operation.llm_metadata.cost == 0.002
    assert operation.llm_metadata.time_seconds == 1.5
    assert operation.tokens == 150
    assert operation.cost == 0.002


def test_operation_setters():
    operation = Operation("value")
    operation.set_kind("mutation")
    operation.set_value("new value")
    operation.set_duration(2.0)
    operation.set_llm_metadata(LLMMetadata(model="claude-sonnet-4", tokens_in=10, tokens_out=20))

    assert operation.kind == "mutation"
    assert operation.value == "new value"
    assert operation.duration_seconds == 2.0
    assert operation.tokens == 30


def test_llm_metadata_from_ai_message_usage_metadata():
    """Standardized usage_metadata field is preferred, model from model_name (OpenAI)."""
    message = AIMessage(
        content="hello",
        usage_metadata={"input_tokens": 120, "output_tokens": 30, "total_tokens": 150},
        response_metadata={"model_name": "gpt-4o-mini"},
    )
    metadata = LLMMetadata.from_ai_message(message, time_seconds=0.8, cost=0.001)
    assert metadata.model == "gpt-4o-mini"
    assert metadata.tokens_in == 120
    assert metadata.tokens_out == 30
    assert metadata.total_tokens == 150
    assert metadata.time_seconds == 0.8
    assert metadata.cost == 0.001


def test_llm_metadata_from_ai_message_openai_token_usage():
    """OpenAI response_metadata fallback: token_usage with prompt/completion tokens."""
    message = AIMessage(
        content="hello",
        response_metadata={
            "model_name": "gpt-4o",
            "token_usage": {"prompt_tokens": 200, "completion_tokens": 80},
        },
    )
    metadata = LLMMetadata.from_ai_message(message)
    assert metadata.model == "gpt-4o"
    assert metadata.tokens_in == 200
    assert metadata.tokens_out == 80


def test_llm_metadata_from_ai_message_anthropic_usage():
    """Anthropic response_metadata fallback: usage with input/output tokens."""
    message = AIMessage(
        content="hello",
        response_metadata={
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 90, "output_tokens": 45},
        },
    )
    metadata = LLMMetadata.from_ai_message(message, time_seconds=1.2)
    assert metadata.model == "claude-sonnet-4-20250514"
    assert metadata.tokens_in == 90
    assert metadata.tokens_out == 45
    assert metadata.time_seconds == 1.2


def test_llm_metadata_from_ai_message_unrecognized_shape_raises():
    message = AIMessage(content="hello")
    with pytest.raises(ValueError, match="Unrecognized AIMessage shape"):
        LLMMetadata.from_ai_message(message)


def test_operation_from_ai_message():
    message = AIMessage(
        content="haiku text",
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        response_metadata={"model_name": "gpt-4o-mini"},
    )
    operation = Operation.from_ai_message("haiku text", message, cost=0.0005)
    assert operation.value == "haiku text"
    assert operation.tokens == 15
    assert operation.llm_metadata.model == "gpt-4o-mini"
    assert operation.cost == 0.0005
