from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OperationKind = Literal["crossover", "mutation", "invoke", "evaluate"]


@dataclass(frozen=True)
class OperationRecord:
    kind: OperationKind
    duration_seconds: float
    tokens: int = 0
