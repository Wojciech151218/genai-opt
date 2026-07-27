from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Self

from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.serialization import serialize_value, type_path
from genai_opt.optimizer_engine.utils.typevars import Inv, P

_GENOME_REGISTRY: dict[str, type[Genome[Any, Any]]] = {}


class Genome(ABC, Generic[P, Inv]):
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
        return {
            "genome_type": type_path(self.__class__),
            "phenotype": serialize_value(self.phenotype),
            "evaluation": self._evaluation,
            "invocation": serialize_value(self._invocation),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        genome_type = data.get("genome_type")
        if genome_type and genome_type != type_path(cls):
            target = _GENOME_REGISTRY.get(genome_type)
            if target is None:
                raise ValueError(f"Unknown genome type: {genome_type}")
            return target.from_json(data, **context)  # type: ignore[return-value]
        return cls._from_json(data, **context)

    @classmethod
    def _from_json(cls, data: dict[str, Any], **context: Any) -> Self:
        raise NotImplementedError(f"{cls.__name__}._from_json() is not implemented")

    def _restore_runtime_state(self, data: dict[str, Any], invocation_schema: type[Inv] | None = None) -> None:
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
        if self._invocation is None:
            raise ValueError("Genome has not been invoked")
        return self._invocation

    @property
    def evaluation(self) -> float:
        if self._evaluation is None:
            raise ValueError("Genome has not been evaluated")
        return self._evaluation

    def reset_invocations(self) -> None:
        self._invocation = None

    def _set_invocation(self, invocation: Inv) -> None:
        self._invocation = invocation

    def reset_evaluation(self) -> None:
        self._evaluation = None

    def _set_evaluation(self, value: float) -> None:
        self._evaluation = value

    @abstractmethod
    async def invoke(self) -> Operation[Inv]:
        raise NotImplementedError("Genome.invoke() is not implemented")

    @abstractmethod
    async def evaluate(self) -> Operation[float]:
        raise NotImplementedError("Genome.evaluate() is not implemented")

    @abstractmethod
    async def mutate(self) -> Operation[Self]:
        raise NotImplementedError("Genome.mutate() is not implemented")

    @abstractmethod
    async def crossover(self, other: Genome[P, Inv]) -> Operation[Self]:
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
