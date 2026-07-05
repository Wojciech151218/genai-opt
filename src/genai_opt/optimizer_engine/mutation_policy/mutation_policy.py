from __future__ import annotations

from random import random

from genai_opt.optimizer_engine.utils.types import Types as T


def random_mutation(threshold: float) -> T.MutationPolicy:
    def should_mutate(genome: T.Genome) -> bool:
        return random() < threshold

    return should_mutate
