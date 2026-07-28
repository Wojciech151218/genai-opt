"""A chat model that returns scripted structured replies, for tests.

Every LLM-backed operation in the library goes through
``with_structured_output(schema, include_raw=True)`` followed by an invoke, so
overriding that one method is enough to run a whole experiment offline. That is
also how a user would plug in a recorded or stubbed model.
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from genai_opt.adapters.simple_system_prompt_genome.types import (
    EvaluationScore,
    SystemPromptMutation,
)
from genai_opt.experiments.haiku_experiment import HaikuEvaluation, HaikuOutput

VALID_HAIKU = HaikuOutput(
    line_one="An old silent pond",
    line_two="A frog jumps into the pond",
    line_three="Splash! Silence again",
)

MALFORMED_HAIKU = HaikuOutput(
    line_one="An old pond",
    line_two="A frog jumps",
    line_three="Splash",
)


def default_reply(schema: type[BaseModel]) -> BaseModel:
    """Return a plausible reply for one of the library's structured schemas."""
    if schema is HaikuOutput:
        return VALID_HAIKU
    if schema is HaikuEvaluation:
        return HaikuEvaluation(cultural_reference=["hanami", "kigo"], significance=60)
    if schema is SystemPromptMutation:
        return SystemPromptMutation(system_prompt="Write a haiku steeped in seasonal tradition.")
    if schema is EvaluationScore:
        return EvaluationScore(score=42.0)
    raise AssertionError(f"No scripted reply for schema {schema!r}")


class FakeChatModel(BaseChatModel):
    """A chat model whose structured replies are scripted rather than generated.

    Attributes:
        model: Reported as the model name, so checkpoint round-trips have
            something to store.
        temperature: Reported alongside the model name.
        replies: Overrides per schema, keyed by schema class. Values may be a
            model instance or a callable taking the schema.
        parsing_error: When set, every structured call reports this as a parsing
            failure instead of returning a value.
        requested_schemas: Names of the schemas asked for, in call order.
    """

    model: str = "fake-model"
    temperature: float = 0.0
    replies: dict[Any, Any] = Field(default_factory=dict)
    parsing_error: Any = None
    requested_schemas: list[str] = Field(default_factory=list)
    tokens_in: int = 11
    tokens_out: int = 7

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError("FakeChatModel only supports structured output")

    def with_structured_output(self, schema, **kwargs):
        """Return a runnable that produces a scripted ``include_raw`` payload."""
        self.requested_schemas.append(getattr(schema, "__name__", str(schema)))

        def respond(_: Any) -> dict[str, Any]:
            raw = AIMessage(
                content="",
                response_metadata={
                    "model_name": self.model,
                    "token_usage": {
                        "prompt_tokens": self.tokens_in,
                        "completion_tokens": self.tokens_out,
                    },
                },
            )
            if self.parsing_error is not None:
                return {"raw": raw, "parsed": None, "parsing_error": self.parsing_error}
            return {"raw": raw, "parsed": self._reply_for(schema), "parsing_error": None}

        return RunnableLambda(respond)

    def _reply_for(self, schema: Any) -> Any:
        override = self.replies.get(schema)
        if override is None:
            return default_reply(schema)
        return override(schema) if callable(override) else override
