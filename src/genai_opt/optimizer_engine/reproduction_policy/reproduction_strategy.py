from __future__ import annotations

from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T


def generational_reproduction(
    population_size: int,
) -> T.ReproductionStrategy:
    def bind(select_parents: T.ParentSelection) -> T.ReproduceFn:
        async def reproduce(population: T.Population) -> tuple[T.Population, list[Operation]]:
            new_population = Population()
            operations: list[Operation] = []
            while new_population.get_genome_count() < population_size:
                parent_a, parent_b = select_parents(population)
                operation = await parent_a._crossover(parent_b)
                operations.append(operation)
                new_population.add_genome(operation.value)
            return new_population, operations

        return reproduce

    return bind
