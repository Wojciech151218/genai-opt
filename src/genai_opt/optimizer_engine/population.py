from __future__ import annotations

from genai_opt.optimizer_engine.genome import Genome
from typing import Callable, TypeVar, List
import asyncio

FITNESS = TypeVar('FITNESS')
PHENOTYPE = TypeVar('PHENOTYPE')

class Population:
    def __init__(self, population: list[Genome[PHENOTYPE, FITNESS]] | None = None):
        self.population: list[Genome[PHENOTYPE, FITNESS]] = (
            [] if population is None else population
        )

    def add_genome(self, genome: Genome[PHENOTYPE,FITNESS]):
        self.population.append(genome)

    def remove_genome(self, index: int):
        self.population.pop(index)

    def loop(self, lambda_function: Callable[[Genome[PHENOTYPE,FITNESS]], None]) -> None:
        for genome in self.population:
            lambda_function(genome)

    async def evaluate_population(self) -> None:
        await asyncio.gather(*[genome.evaluate() for genome in self.population])

    def reset_evaluations(self) -> None:
        for genome in self.population:
            genome.reset_evaluation()

    type GenomeAndFitness = tuple[Genome[PHENOTYPE,FITNESS], float]

    def get_genome_and_fitness(self, index: int) -> GenomeAndFitness:
        try:
            genome = self.population[index]
        except IndexError:
            raise IndexError(f"Index {index} out of range")
        return genome, genome.evaluation

    def get_genome_fitness(self) -> List[GenomeAndFitness]:
        return [self.get_genome_and_fitness(index) for index in range(len(self.population))]

    def get_genome_count(self) -> int:
        return len(self.population)

    def merge(self, other: 'Population[PHENOTYPE,FITNESS]') -> 'Population[PHENOTYPE,FITNESS]':
        new_population = Population()
        new_population.population = self.population + other.population
        return new_population