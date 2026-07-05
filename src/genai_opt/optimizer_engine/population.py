from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Generic

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.utils.typevars import I, P


class Population(Generic[P, I]):
    def __init__(self, population: list[Genome[P, I]] | None = None):
        self.population: list[Genome[P, I]] = (
            [] if population is None else population
        )

    def add_genome(self, genome: Genome[P, I]) -> None:
        self.population.append(genome)

    def remove_genome(self, index: int) -> None:
        self.population.pop(index)

    def loop(self, lambda_function: Callable[[Genome[P, I]], None]) -> None:
        for genome in self.population:
            lambda_function(genome)

    async def evaluate_population(self) -> None:
        await asyncio.gather(*[genome.evaluate() for genome in self.population])

    def reset_evaluations(self) -> None:
        for genome in self.population:
            genome.reset_evaluation()

    def get_genome_and_fitness(self, index: int) -> tuple[Genome[P, I], float]:
        try:
            genome = self.population[index]
        except IndexError:
            raise IndexError(f"Index {index} out of range")
        return genome, genome.evaluation

    def get_genome_fitness(self) -> list[tuple[Genome[P, I], float]]:
        return [
            self.get_genome_and_fitness(index) for index in range(len(self.population))
        ]

    def get_genome_count(self) -> int:
        return len(self.population)

    def merge(self, other: Population[P, I]) -> Population[P, I]:
        new_population = Population()
        new_population.population = self.population + other.population
        return new_population
