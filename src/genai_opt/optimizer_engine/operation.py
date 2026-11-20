"""Records of individual genome operations, including their LLM usage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID, uuid4

V = TypeVar("V")

OperationKind = Literal["crossover", "mutation", "invoke", "evaluate", "unknown"]
"""Which genome operation produced a value."""


@dataclass
class LLMMetadata:
    """Token counts, model name and cost for a single model call.

    Attributes:
        model: Model that served the call, when the provider reports it.
        cost: Cost in currency units. Nothing computes this automatically; set
            it yourself if you want cost totals.
        time_seconds: How long the model call took.
        tokens_in: Prompt tokens.
        tokens_out: Completion tokens.
    """

    model: str | None = None
    cost: float | None = None
    time_seconds: float | None = None
    tokens_in: int = 0
    tokens_out: int = 0

    @property
    def total_tokens(self) -> int:
        """Prompt plus completion tokens."""
        return self.tokens_in + self.tokens_out

    @classmethod
    def from_ai_message(
        cls,
        message: Any,
        *,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> LLMMetadata:
        """Build metadata from a LangChain ``AIMessage``.

        Token counts are read from the standardized ``usage_metadata`` field
        (``input_tokens`` / ``output_tokens``). If it is absent, falls back to
        the provider-specific ``response_metadata`` payloads: ``token_usage``
        with ``prompt_tokens``/``completion_tokens`` (OpenAI) or ``usage`` with
        ``input_tokens``/``output_tokens`` (Anthropic).

        Args:
            message: The ``AIMessage`` returned by the model.
            time_seconds: How long the call took.
            cost: Cost of the call, if you track it.

        Returns:
            The extracted metadata.

        Raises:
            ValueError: If no recognizable token usage shape is found.
        """
        response_metadata = getattr(message, "response_metadata", None) or {}
        if not isinstance(response_metadata, dict):
            response_metadata = {}
        model = response_metadata.get("model_name") or response_metadata.get("model")

        tokens_in, tokens_out = cls._extract_token_counts(message, response_metadata)
        return cls(
            model=model,
            cost=cost,
            time_seconds=time_seconds,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    @staticmethod
    def _extract_token_counts(message: Any, response_metadata: dict) -> tuple[int, int]:
        usage_metadata = getattr(message, "usage_metadata", None)
        if isinstance(usage_metadata, dict) and ("input_tokens" in usage_metadata or "output_tokens" in usage_metadata):
            return (
                usage_metadata.get("input_tokens", 0) or 0,
                usage_metadata.get("output_tokens", 0) or 0,
            )

        token_usage = response_metadata.get("token_usage")
        if isinstance(token_usage, dict) and ("prompt_tokens" in token_usage or "completion_tokens" in token_usage):
            return (
                token_usage.get("prompt_tokens", 0) or 0,
                token_usage.get("completion_tokens", 0) or 0,
            )

        usage = response_metadata.get("usage")
        if isinstance(usage, dict) and ("input_tokens" in usage or "output_tokens" in usage):
            return (
                usage.get("input_tokens", 0) or 0,
                usage.get("output_tokens", 0) or 0,
            )

        raise ValueError(
            "Unrecognized AIMessage shape: no token usage found in usage_metadata "
            "or response_metadata (expected 'usage_metadata', 'token_usage', or 'usage')"
        )


class Operation(Generic[V]):
    """Result of a single genome operation.

    Carries the operation's value (invocation result, fitness, child genome),
    a random identifier, timing, and optional LLM usage metadata.

    The identifier lets a frontend follow one operation from the moment a
    controller is told about it through to the checkpoint metadata, and it is
    preserved when a phenotype operation is rewrapped as a genome operation.

    Args:
        value: What the operation produced.
        kind: Which operation this was. The engine overwrites this, so genome
            authors rarely set it.
        duration_seconds: Measured duration. The engine fills this in when it is
            left at zero.
        llm_metadata: Usage metadata for the underlying model call.
        model: Convenience field, used to build ``llm_metadata`` when it is not
            given directly.
        cost: Convenience field, as ``model``.
        time_seconds: Convenience field, as ``model``.
        tokens_in: Convenience field, as ``model``.
        tokens_out: Convenience field, as ``model``.
        id: Existing identifier to keep, instead of generating a new one.
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
        """Total tokens used, or ``0`` for operations with no model call."""
        return self.llm_metadata.total_tokens if self.llm_metadata is not None else 0

    @property
    def cost(self) -> float:
        """Cost of this operation, or ``0.0`` when none was recorded."""
        if self.llm_metadata is None or self.llm_metadata.cost is None:
            return 0.0
        return self.llm_metadata.cost

    def set_kind(self, kind: OperationKind) -> None:
        """Label which genome operation produced this value."""
        self.kind = kind

    def set_value(self, value: V) -> None:
        """Replace the produced value."""
        self.value = value

    def set_duration(self, duration_seconds: float) -> None:
        """Record how long the operation took."""
        self.duration_seconds = duration_seconds

    def set_llm_metadata(self, llm_metadata: LLMMetadata) -> None:
        """Attach usage metadata for the underlying model call."""
        self.llm_metadata = llm_metadata

    @classmethod
    def from_ai_message(
        cls,
        value: V,
        message: Any,
        *,
        kind: OperationKind = "unknown",
        duration_seconds: float = 0.0,
        time_seconds: float | None = None,
        cost: float | None = None,
    ) -> Operation[V]:
        """Build an operation with usage metadata read from a LangChain message.

        Args:
            value: What the operation produced.
            message: The ``AIMessage`` that produced it.
            kind: Which operation this was.
            duration_seconds: Measured duration.
            time_seconds: Duration of the model call itself.
            cost: Cost of the call, if you track it.

        Returns:
            The operation, with token counts and model name filled in.

        Raises:
            ValueError: If the message carries no recognizable token usage.
        """
        return cls(
            value,
            kind=kind,
            duration_seconds=duration_seconds,
            llm_metadata=LLMMetadata.from_ai_message(message, time_seconds=time_seconds, cost=cost),
        )

    def __repr__(self) -> str:
        return (
            f"Operation(id={self.id}, kind={self.kind!r}, "
            f"duration_seconds={self.duration_seconds:.4f}, tokens={self.tokens})"
        )
