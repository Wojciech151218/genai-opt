"""Tests for Operation and LLMMetadata."""

from types import SimpleNamespace

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


def test_llm_metadata_from_openai():
    response = SimpleNamespace(
        model="gpt-4o-mini",
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30),
    )
    metadata = LLMMetadata.from_openai(response, time_seconds=0.8, cost=0.001)
    assert metadata.model == "gpt-4o-mini"
    assert metadata.tokens_in == 120
    assert metadata.tokens_out == 30
    assert metadata.total_tokens == 150
    assert metadata.time_seconds == 0.8
    assert metadata.cost == 0.001


def test_llm_metadata_from_openai_responses_api():
    response = SimpleNamespace(
        model="gpt-4o",
        usage=SimpleNamespace(input_tokens=200, output_tokens=80),
    )
    metadata = LLMMetadata.from_openai(response)
    assert metadata.tokens_in == 200
    assert metadata.tokens_out == 80


def test_llm_metadata_from_anthropic():
    message = SimpleNamespace(
        model="claude-sonnet-4-20250514",
        usage=SimpleNamespace(input_tokens=90, output_tokens=45),
    )
    metadata = LLMMetadata.from_anthropic(message, time_seconds=1.2)
    assert metadata.model == "claude-sonnet-4-20250514"
    assert metadata.tokens_in == 90
    assert metadata.tokens_out == 45
    assert metadata.time_seconds == 1.2


def test_operation_from_openai():
    response = SimpleNamespace(
        model="gpt-4o-mini",
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )
    operation = Operation.from_openai("haiku text", response)
    assert operation.value == "haiku text"
    assert operation.tokens == 15
    assert operation.llm_metadata.model == "gpt-4o-mini"


def test_operation_from_anthropic():
    message = SimpleNamespace(
        model="claude-sonnet-4-20250514",
        usage=SimpleNamespace(input_tokens=7, output_tokens=3),
    )
    operation = Operation.from_anthropic(42.0, message, cost=0.0005)
    assert operation.value == 42.0
    assert operation.tokens == 10
    assert operation.cost == 0.0005
