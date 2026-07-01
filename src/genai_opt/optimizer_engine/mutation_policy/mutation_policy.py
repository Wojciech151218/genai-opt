from __future__ import annotations

from random import random
from typing import Callable, TypeVar

from genai_opt.optimizer_engine.genome import Genome

INVOCATION = TypeVar("INVOCATION")
PHENOTYPE = TypeVar("PHENOTYPE")


def random_mutation(
    threshold: float,
) -> Callable[[Genome[PHENOTYPE, INVOCATION]], bool]:
    def should_mutate(genome: Genome[PHENOTYPE, INVOCATION]) -> bool:
        return random() < threshold

    return should_mutate
