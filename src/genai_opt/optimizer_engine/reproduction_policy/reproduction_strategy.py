from __future__ import annotations

from collections.abc import Awaitable, Callable

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.population import Population

type ParentPair = tuple[Genome, Genome]
type SelectParents = Callable[[Population], ParentPair]


def generational_reproduction(
    population_size: int,
    select_parents: SelectParents,
) -> Callable[[Population], Awaitable[Population]]:
    async def reproduce(population: Population) -> Population:
        new_population = Population()
        while new_population.get_genome_count() < population_size:
            parent_a, parent_b = select_parents(population)
            child = await parent_a.crossover(parent_b)
            new_population.add_genome(child)
        return new_population

    return reproduce
