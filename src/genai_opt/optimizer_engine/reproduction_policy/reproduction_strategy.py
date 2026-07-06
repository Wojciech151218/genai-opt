from __future__ import annotations

import time

from genai_opt.optimizer_engine.operation_record import OperationRecord
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T


def generational_reproduction(
    population_size: int,
) -> T.ReproductionStrategy:
    def bind(select_parents: T.ParentSelection) -> T.ReproduceFn:
        async def reproduce(population: T.Population) -> tuple[T.Population, list[OperationRecord]]:
            new_population = Population()
            operations: list[OperationRecord] = []
            while new_population.get_genome_count() < population_size:
                parent_a, parent_b = select_parents(population)
                start = time.perf_counter()
                child = await parent_a.crossover(parent_b)
                duration = time.perf_counter() - start
                tokens = parent_a.last_operation_tokens
                parent_a._clear_operation_tokens()
                operations.append(OperationRecord("crossover", duration, tokens))
                new_population.add_genome(child)
            return new_population, operations

        return reproduce

    return bind
