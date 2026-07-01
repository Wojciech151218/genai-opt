from __future__ import annotations

from random import choices

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import (
    ParentPair,
)


def roulette_wheel_selection(population: Population) -> ParentPair:
    total_fitness = sum(genome.evaluation for genome in population.population)
    selection_probabilities = [
        genome.evaluation / total_fitness for genome in population.population
    ]
    parents = []
    for _ in range(2):
        parent = choices(
            population.population, weights=selection_probabilities, k=1
        )[0]
        parents.append(parent)
    return parents[0], parents[1]


def tournament_selection(population: Population) -> ParentPair:
    parents = []
    for _ in range(2):
        tournament = choices(population.population, k=2)
        parent = max(tournament, key=lambda genome: genome.evaluation)
        parents.append(parent)
    return parents[0], parents[1]


def rank_selection(population: Population) -> ParentPair:
    best = max(population.population, key=lambda genome: genome.evaluation)
    return best, best
