from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Generic

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation_record import OperationRecord
from genai_opt.optimizer_engine.utils.typevars import Inv, P


async def _timed_invoke(genome: Genome[P, Inv]) -> OperationRecord:
    start = time.perf_counter()
    await genome._invoke()
    duration = time.perf_counter() - start
    tokens = genome.last_operation_tokens
    genome._clear_operation_tokens()
    return OperationRecord("invoke", duration, tokens)


async def _timed_evaluate(genome: Genome[P, Inv]) -> OperationRecord:
    start = time.perf_counter()
    await genome._evaluate()
    duration = time.perf_counter() - start
    tokens = genome.last_operation_tokens
    genome._clear_operation_tokens()
    return OperationRecord("evaluate", duration, tokens)


class Population(Generic[P, Inv]):
    def __init__(self, population: list[Genome[P, Inv]] | None = None):
        self.population: list[Genome[P, Inv]] = [] if population is None else population

    def add_genome(self, genome: Genome[P, Inv]) -> None:
        self.population.append(genome)

    def remove_genome(self, index: int) -> None:
        self.population.pop(index)

    def loop(self, lambda_function: Callable[[Genome[P, Inv]], None]) -> None:
        for genome in self.population:
            lambda_function(genome)

    async def evaluate_population(self) -> list[OperationRecord]:
        invoke_operations = await asyncio.gather(*[_timed_invoke(genome) for genome in self.population])
        evaluate_operations = await asyncio.gather(
            *[_timed_evaluate(genome) for genome in self.population]
        )
        return list(invoke_operations) + list(evaluate_operations)

    def reset_evaluations(self) -> None:
        for genome in self.population:
            genome.reset_evaluation()

    def get_genome_and_fitness(self, index: int) -> tuple[Genome[P, Inv], float]:
        try:
            genome = self.population[index]
        except IndexError:
            raise IndexError(f"Index {index} out of range") from None
        return genome, genome.evaluation

    def get_genome_fitness(self) -> list[tuple[Genome[P, Inv], float]]:
        return [self.get_genome_and_fitness(index) for index in range(len(self.population))]

    def get_genome_count(self) -> int:
        return len(self.population)

    def merge(self, other: Population[P, Inv]) -> Population[P, Inv]:
        new_population = Population()
        new_population.population = self.population + other.population
        return new_population
