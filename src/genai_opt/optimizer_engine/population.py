from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any, Generic

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Population(Generic[P, Inv]):
    def __init__(self, population: list[Genome[P, Inv]] | None = None):
        self.population: list[Genome[P, Inv]] = [] if population is None else population

    def to_json(self) -> list[dict[str, Any]]:
        return [genome.to_json() for genome in self.population]

    @classmethod
    def from_json(cls, data: list[dict[str, Any]], **context: Any) -> Population[P, Inv]:
        return cls([Genome.from_json(genome_data, **context) for genome_data in data])

    def add_genome(self, genome: Genome[P, Inv]) -> None:
        self.population.append(genome)

    def remove_genome(self, index: int) -> None:
        self.population.pop(index)

    def loop(self, lambda_function: Callable[[Genome[P, Inv]], None]) -> None:
        for genome in self.population:
            lambda_function(genome)

    async def evaluate_population(self) -> list[Operation]:
        return [operation async for operation in self.evaluate_population_stream()]

    async def evaluate_population_stream(self) -> AsyncIterator[Operation]:
        """Yield each genome's invocation and evaluation as they complete.

        A genome begins evaluation immediately after its own invocation. Other
        genomes continue invoking or evaluating concurrently.
        """
        operations: asyncio.Queue[Operation | BaseException] = asyncio.Queue()

        async def invoke_and_evaluate(genome: Genome[P, Inv]) -> None:
            try:
                await operations.put(await genome._invoke())
                await operations.put(await genome._evaluate())
            except BaseException as error:
                await operations.put(error)

        tasks = [asyncio.create_task(invoke_and_evaluate(genome)) for genome in self.population]
        try:
            for _ in range(2 * len(tasks)):
                operation = await operations.get()
                if isinstance(operation, BaseException):
                    raise operation
                yield operation
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

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
