"""Policies deciding which offspring are mutated."""

from __future__ import annotations

from random import random

from genai_opt.optimizer_engine.utils.types import Types as T


def random_mutation(threshold: float) -> T.MutationPolicy:
    """Mutate each offspring independently with probability ``threshold``.

    The decision ignores the genome, so every candidate is equally likely to be
    mutated. With LLM-backed genomes each mutation is a model call, which makes
    this the main lever on the cost of an iteration.

    Args:
        threshold: Mutation probability per genome. ``0.0`` disables mutation
            and ``1.0`` mutates every offspring.

    Returns:
        A policy the engine calls once per offspring genome.
    """

    def should_mutate(genome: T.Genome) -> bool:
        return random() < threshold

    return should_mutate
