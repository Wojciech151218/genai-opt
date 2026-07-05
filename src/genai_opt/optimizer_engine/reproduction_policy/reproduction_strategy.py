from __future__ import annotations

from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T


def generational_reproduction(
    population_size: int,
) -> T.ReproductionStrategy:
    def bind(select_parents: T.ParentSelection) -> T.ReproduceFn:
        async def reproduce(population: T.Population) -> T.Population:
            new_population = Population()
            while new_population.get_genome_count() < population_size:
                parent_a, parent_b = select_parents(population)
                child = await parent_a.crossover(parent_b)
                new_population.add_genome(child)
            return new_population

        return reproduce

    return bind
