"""Strategies for picking the two parents of each new genome.

Every strategy here reads ``genome.evaluation``, so the population must already
be evaluated. The engine guarantees that: reproduction always follows an
evaluation phase.
"""

from __future__ import annotations

from random import choices

from genai_opt.optimizer_engine.utils.types import Types as T


def roulette_wheel_selection(population: T.Population) -> T.ParentPair:
    """Pick two parents with probability proportional to fitness.

    Keeps weak genomes in play, which preserves diversity, but assumes fitness
    values are non-negative and do not sum to zero.

    Args:
        population: An evaluated population.

    Returns:
        Two parents, possibly the same genome twice.

    Raises:
        ValueError: If any genome has not been evaluated.
        ZeroDivisionError: If the fitness values sum to zero.
    """
    total_fitness = sum(genome.evaluation for genome in population.population)
    selection_probabilities = [genome.evaluation / total_fitness for genome in population.population]
    parents = []
    for _ in range(2):
        parent = choices(population.population, weights=selection_probabilities, k=1)[0]
        parents.append(parent)
    return parents[0], parents[1]


def tournament_selection(population: T.Population) -> T.ParentPair:
    """Pick two parents, each as the fitter of two randomly drawn genomes.

    The usual default: it applies steady selection pressure without depending on
    the scale or sign of fitness values.

    Args:
        population: An evaluated population.

    Returns:
        Two parents, possibly the same genome twice.

    Raises:
        ValueError: If any genome has not been evaluated.
    """
    parents = []
    for _ in range(2):
        tournament = choices(population.population, k=2)
        parent = max(tournament, key=lambda genome: genome.evaluation)
        parents.append(parent)
    return parents[0], parents[1]


def rank_selection(population: T.Population) -> T.ParentPair:
    """Return the fittest genome as both parents.

    Purely exploitative, so a population reproduced this way converges on one
    lineage quickly and loses diversity.

    Args:
        population: An evaluated population.

    Returns:
        The fittest genome twice.

    Raises:
        ValueError: If any genome has not been evaluated.
    """
    best = max(population.population, key=lambda genome: genome.evaluation)
    return best, best
