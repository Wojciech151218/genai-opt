"""Timing helpers that turn adapter callbacks into :class:`Operation` values."""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Generic, ParamSpec, TypeAlias, TypeVar, overload

from genai_opt.optimizer_engine.operation import Operation

P = ParamSpec("P")
R = TypeVar("R")
V = TypeVar("V")


@dataclass(frozen=True)
class AdapterResult(Generic[V]):
    """Domain value from a callback, with optional raw LLM payload."""

    value: V
    raw: Any | None = None


Outcome: TypeAlias = V | AdapterResult[V]


def build_operation(
    value: V,
    result: Any,
    *,
    time_seconds: float | None = None,
) -> Operation[V]:
    """Wrap a value in an Operation, attaching LLM metadata from the raw AIMessage.

    Applies ``Operation.from_ai_message`` when the ``include_raw=True`` result
    carries a raw message with a recognizable usage shape; falls back to a bare
    Operation otherwise.
    """
    raw_message = result.get("raw") if isinstance(result, dict) else None
    if raw_message is not None:
        try:
            return Operation.from_ai_message(value, raw_message, time_seconds=time_seconds)
        except ValueError:
            pass
    return Operation(value)


def _outcome_to_operation(outcome: Outcome[V], elapsed: float) -> Operation[V]:
    if isinstance(outcome, AdapterResult):
        operation = build_operation(outcome.value, outcome.raw, time_seconds=elapsed)
    else:
        operation = Operation(outcome)
    operation.set_duration(elapsed)
    return operation


@overload
def timed_operation(fn: Callable[P, Awaitable[Outcome[R]]]) -> Callable[P, Awaitable[Operation[R]]]: ...


@overload
def timed_operation(fn: Callable[P, Outcome[R]]) -> Callable[P, Operation[R]]: ...


def timed_operation(fn: Callable[P, Any]) -> Callable[P, Any]:
    """Time a callback and wrap its return value in an ``Operation``."""
    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Operation[Any]:
            start = time.perf_counter()
            outcome = await fn(*args, **kwargs)
            return _outcome_to_operation(outcome, time.perf_counter() - start)

        return async_wrapper

    @wraps(fn)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Operation[Any]:
        start = time.perf_counter()
        outcome = fn(*args, **kwargs)
        return _outcome_to_operation(outcome, time.perf_counter() - start)

    return sync_wrapper
