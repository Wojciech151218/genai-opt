"""The base class every optimization candidate derives from."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Self

from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.serialization import serialize_value, type_path
from genai_opt.optimizer_engine.utils.typevars import Inv, P

_GENOME_REGISTRY: dict[str, type[Genome[Any, Any]]] = {}


class Genome(ABC, Generic[P, Inv]):
    """One candidate solution, and the four operations the engine performs on it.

    A genome carries a ``phenotype`` (the representation being optimized) and
    knows how to :meth:`invoke` it, :meth:`evaluate` the result into a fitness,
    and produce children by :meth:`mutate` and :meth:`crossover`. Invocation is
    kept separate from evaluation because for LLM work the two are distinct
    calls, and only the invocation output is worth serializing.

    Two generic parameters describe a subclass: ``P`` is the phenotype type and
    ``Inv`` the type produced by invoking it.

    Every concrete subclass is registered automatically when it is defined, so
    :meth:`from_json` can route a checkpoint back to the right class without the
    caller naming it.

    Args:
        phenotype: The representation being optimized.
    """

    genome_type: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", None):
            _GENOME_REGISTRY[type_path(cls)] = cls  # type: ignore[assignment]

    def __init__(self, phenotype: P):
        self.phenotype = phenotype
        self._evaluation: float | None = None
        self._invocation: Inv | None = None

    def to_json(self) -> dict[str, Any]:
        """Serialize this genome for a checkpoint.

        Subclasses should extend the result rather than replace it, as in
        ``{**super().to_json(), "target": self.target}``, so the type tag and
        runtime state survive.
        """
        return {
            "genome_type": type_path(self.__class__),
            "phenotype": serialize_value(self.phenotype),
            "evaluation": self._evaluation,
            "invocation": serialize_value(self._invocation),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        """Rebuild a genome from a checkpoint payload.

        The payload's type tag decides which registered subclass is used, so
        calling this on :class:`Genome` itself is enough to restore a mixed
        population.

        Args:
            data: A payload previously produced by :meth:`to_json`.
            **context: Collaborators that cannot be serialized, such as a chat
                model or the evaluation function, forwarded to the subclass.

        Returns:
            The restored genome, including any stored fitness and invocation.

        Raises:
            ValueError: If the payload names a genome type that is not
                registered, usually because the module defining it has not been
                imported.
        """
        genome_type = data.get("genome_type")
        if genome_type and genome_type != type_path(cls):
            target = _GENOME_REGISTRY.get(genome_type)
            if target is None:
                raise ValueError(f"Unknown genome type: {genome_type}")
            return target.from_json(data, **context)  # type: ignore[return-value]
        return cls._from_json(data, **context)

    @classmethod
    def _from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        """Rebuild an instance of this specific subclass.

        Override this, not :meth:`from_json`, and finish by calling
        :meth:`_restore_runtime_state` so the stored fitness and invocation come
        back too. Only needed by genomes that will be checkpointed.
        """
        raise NotImplementedError(f"{cls.__name__}._from_json() is not implemented")

    def _restore_runtime_state(self, data: dict[str, Any], invocation_schema: type[Inv] | None = None) -> None:
        """Reapply the fitness and invocation recorded in a checkpoint.

        Args:
            data: The payload being restored.
            invocation_schema: Pydantic model used to validate the stored
                invocation back into an object. Without it the raw JSON value is
                kept as-is.
        """
        evaluation = data.get("evaluation")
        if evaluation is not None:
            self._set_evaluation(float(evaluation))

        invocation = data.get("invocation")
        if invocation is None:
            return

        if invocation_schema is not None and hasattr(invocation_schema, "model_validate"):
            from genai_opt.optimizer_engine.serialization import deserialize_value

            self._set_invocation(deserialize_value(invocation_schema, invocation))
        else:
            self._set_invocation(invocation)  # type: ignore[arg-type]

    @property
    def invocation(self) -> Inv:
        """The result of the most recent invocation.

        Raises:
            ValueError: If this genome has not been invoked yet.
        """
        if self._invocation is None:
            raise ValueError("Genome has not been invoked")
        return self._invocation

    @property
    def evaluation(self) -> float:
        """This genome's fitness, where higher is better.

        Raises:
            ValueError: If this genome has not been evaluated yet.
        """
        if self._evaluation is None:
            raise ValueError("Genome has not been evaluated")
        return self._evaluation

    def reset_invocations(self) -> None:
        """Forget the stored invocation result."""
        self._invocation = None

    def _set_invocation(self, invocation: Inv) -> None:
        self._invocation = invocation

    def reset_evaluation(self) -> None:
        """Forget the stored fitness."""
        self._evaluation = None

    def _set_evaluation(self, value: float) -> None:
        self._evaluation = value

    @abstractmethod
    async def invoke(self) -> Operation[Inv]:
        """Run the phenotype and produce the output that will be scored.

        For an LLM genome this is the model call. The engine stores the returned
        value, so :meth:`evaluate` can score it without invoking again.
        """
        raise NotImplementedError("Genome.invoke() is not implemented")

    @abstractmethod
    async def evaluate(self) -> Operation[float]:
        """Score the stored invocation, higher being better.

        Read the output from :attr:`invocation`; the engine always invokes first.
        """
        raise NotImplementedError("Genome.evaluate() is not implemented")

    @abstractmethod
    async def mutate(self) -> Operation[Self]:
        """Return a new genome derived from this one by a random change.

        Must not modify this genome. Children start unevaluated.
        """
        raise NotImplementedError("Genome.mutate() is not implemented")

    @abstractmethod
    async def crossover(self, other: Genome[P, Inv]) -> Operation[Self]:
        """Return a new genome combining this one with ``other``.

        Must modify neither parent. Children start unevaluated.
        """
        raise NotImplementedError("Genome.crossover() is not implemented")

    @staticmethod
    async def _timed(operation_coroutine, kind: OperationKind) -> Operation:
        start = time.perf_counter()
        operation = await operation_coroutine
        duration = time.perf_counter() - start
        operation.set_kind(kind)
        if operation.duration_seconds == 0.0:
            operation.set_duration(duration)
        return operation

    async def _invoke(self) -> Operation[Inv]:
        operation = await self._timed(self.invoke(), "invoke")
        self._set_invocation(operation.value)
        return operation

    async def _evaluate(self) -> Operation[float]:
        operation = await self._timed(self.evaluate(), "evaluate")
        self._set_evaluation(operation.value)
        return operation

    async def _mutate(self) -> Operation[Self]:
        return await self._timed(self.mutate(), "mutation")

    async def _crossover(self, other: Genome[P, Inv]) -> Operation[Self]:
        return await self._timed(self.crossover(other), "crossover")
