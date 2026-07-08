from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID, uuid4

V = TypeVar("V")

OperationKind = Literal["crossover", "mutation", "invoke", "evaluate", "unknown"]


@dataclass
class LLMMetadata:
    model: str | None = None
    cost: float | None = None
    time_seconds: float | None = None
    tokens_in: int = 0
    tokens_out: int = 0

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out

    @classmethod
    def from_openai(
        cls,
        response: Any,
        *,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> LLMMetadata:
        """Build metadata from an OpenAI chat completion or Responses API result."""
        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", None)
        if tokens_in is None:
            tokens_in = getattr(usage, "input_tokens", 0) or 0
        tokens_out = getattr(usage, "completion_tokens", None)
        if tokens_out is None:
            tokens_out = getattr(usage, "output_tokens", 0) or 0
        return cls(
            model=getattr(response, "model", None),
            cost=cost,
            time_seconds=time_seconds,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    @classmethod
    def from_anthropic(
        cls,
        message: Any,
        *,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> LLMMetadata:
        """Build metadata from an Anthropic Messages API result."""
        usage = getattr(message, "usage", None)
        return cls(
            model=getattr(message, "model", None),
            cost=cost,
            time_seconds=time_seconds,
            tokens_in=getattr(usage, "input_tokens", 0) or 0,
            tokens_out=getattr(usage, "output_tokens", 0) or 0,
        )


class Operation(Generic[V]):
    """Result of a single genome operation.

    Carries the operation's value (invocation result, fitness, child genome),
    a random identifier, timing, and optional LLM usage metadata.
    """

    def __init__(
        self,
        value: V,
        kind: OperationKind = "unknown",
        duration_seconds: float = 0.0,
        llm_metadata: LLMMetadata | None = None,
        *,
        model: str | None = None,
        cost: float | None = None,
        time_seconds: float | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        id: UUID | None = None,
    ):
        self.id: UUID = uuid4() if id is None else id
        self.kind: OperationKind = kind
        self.value: V = value
        self.duration_seconds: float = duration_seconds

        # Elastic constructor: raw LLM fields build the metadata object inline.
        if llm_metadata is None and any(
            argument is not None for argument in (model, cost, time_seconds, tokens_in, tokens_out)
        ):
            llm_metadata = LLMMetadata(
                model=model,
                cost=cost,
                time_seconds=time_seconds,
                tokens_in=tokens_in or 0,
                tokens_out=tokens_out or 0,
            )
        self.llm_metadata: LLMMetadata | None = llm_metadata

    @property
    def tokens(self) -> int:
        return self.llm_metadata.total_tokens if self.llm_metadata is not None else 0

    @property
    def cost(self) -> float:
        if self.llm_metadata is None or self.llm_metadata.cost is None:
            return 0.0
        return self.llm_metadata.cost

    def set_kind(self, kind: OperationKind) -> None:
        self.kind = kind

    def set_value(self, value: V) -> None:
        self.value = value

    def set_duration(self, duration_seconds: float) -> None:
        self.duration_seconds = duration_seconds

    def set_llm_metadata(self, llm_metadata: LLMMetadata) -> None:
        self.llm_metadata = llm_metadata

    @classmethod
    def from_openai(
        cls,
        value: V,
        response: Any,
        *,
        kind: OperationKind = "unknown",
        duration_seconds: float = 0.0,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> Operation[V]:
        return cls(
            value,
            kind=kind,
            duration_seconds=duration_seconds,
            llm_metadata=LLMMetadata.from_openai(response, time_seconds=time_seconds, cost=cost),
        )

    @classmethod
    def from_anthropic(
        cls,
        value: V,
        message: Any,
        *,
        kind: OperationKind = "unknown",
        duration_seconds: float = 0.0,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> Operation[V]:
        return cls(
            value,
            kind=kind,
            duration_seconds=duration_seconds,
            llm_metadata=LLMMetadata.from_anthropic(message, time_seconds=time_seconds, cost=cost),
        )

    def __repr__(self) -> str:
        return (
            f"Operation(id={self.id}, kind={self.kind!r}, "
            f"duration_seconds={self.duration_seconds:.4f}, tokens={self.tokens})"
        )
