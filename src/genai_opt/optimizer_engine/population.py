"""A collection of genomes and the operations that act on all of them."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any, Generic

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Population(Generic[P, Inv]):
    """One generation of candidate solutions.

    Args:
        population: The genomes to start with. Defaults to an empty generation.
    """

    def __init__(self, population: list[Genome[P, Inv]] | None = None):
        self.population: list[Genome[P, Inv]] = [] if population is None else population

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize every genome for checkpointing."""
        return [genome.to_json() for genome in self.population]

    @classmethod
    def from_json(cls, data: list[dict[str, Any]], **context: Any) -> Population[P, Inv]:
        """Rebuild a population from serialized genomes.

        Args:
            data: Genome payloads previously produced by :meth:`to_json`.
            **context: Collaborators that genomes cannot serialize, such as a
                chat model or the evaluation function, forwarded to each
                genome's deserializer.

        Returns:
            The restored population.
        """
        return cls([Genome.from_json(genome_data, **context) for genome_data in data])

    def add_genome(self, genome: Genome[P, Inv]) -> None:
        """Append a genome to this generation."""
        self.population.append(genome)

    def remove_genome(self, index: int) -> None:
        """Remove the genome at ``index``.

        Raises:
            IndexError: If ``index`` is out of range.
        """
        self.population.pop(index)

    def loop(self, lambda_function: Callable[[Genome[P, Inv]], None]) -> None:
        """Apply ``lambda_function`` to every genome in order."""
        for genome in self.population:
            lambda_function(genome)

    async def evaluate_population(self) -> list[Operation]:
        """Invoke and evaluate every genome, returning all operations at once.

        Use :meth:`evaluate_population_stream` instead when you want to observe
        or log progress while a slow LLM-backed generation is still running.
        """
        return [operation async for operation in self.evaluate_population_stream()]

    async def evaluate_population_stream(self) -> AsyncIterator[Operation]:
        """Yield each genome's invocation and evaluation as they complete.

        A genome begins evaluation immediately after its own invocation. Other
        genomes continue invoking or evaluating concurrently.

        Yields:
            Two operations per genome, an invoke followed by an evaluate, in
            completion order rather than population order.

        Raises:
            BaseException: The first error raised by any genome. Remaining tasks
                are cancelled before it propagates.
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
        """Discard every stored fitness, so genomes must be evaluated again."""
        for genome in self.population:
            genome.reset_evaluation()

    def get_genome_and_fitness(self, index: int) -> tuple[Genome[P, Inv], float]:
        """Return one genome with its fitness.

        Raises:
            IndexError: If ``index`` is out of range.
            ValueError: If that genome has not been evaluated yet.
        """
        try:
            genome = self.population[index]
        except IndexError:
            raise IndexError(f"Index {index} out of range") from None
        return genome, genome.evaluation

    def get_genome_fitness(self) -> list[tuple[Genome[P, Inv], float]]:
        """Pair every genome with its fitness.

        Handy for picking a winner, for example
        ``max(population.get_genome_fitness(), key=lambda item: item[1])``.

        Raises:
            ValueError: If any genome has not been evaluated yet.
        """
        return [self.get_genome_and_fitness(index) for index in range(len(self.population))]

    def get_genome_count(self) -> int:
        """Return how many genomes this generation holds."""
        return len(self.population)

    def merge(self, other: Population[P, Inv]) -> Population[P, Inv]:
        """Return a new population holding this one's genomes followed by ``other``'s.

        The genomes themselves are shared, not copied, so neither source
        population is modified but the genome objects are not independent.
        """
        new_population = Population()
        new_population.population = self.population + other.population
        return new_population
