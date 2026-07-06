"""Tests for generational_reproduction."""

import asyncio

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import (
    tournament_selection,
)
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import (
    generational_reproduction,
)


def test_generational_reproduction_size():
    """Reproduced population should contain exactly 5 genomes."""
    pop = Population()
    for val in [10.0, 20.0, 30.0, 40.0, 50.0]:
        pop.add_genome(FloatGenome(val, target=50.0))
    asyncio.run(pop.evaluate_population())

    reproduce = generational_reproduction(5)(tournament_selection)
    new_pop = asyncio.run(reproduce(pop))
    assert new_pop.get_genome_count() == 5
