from __future__ import annotations

from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.types import Types as T


def initial_Population_from_list(list: list[T.Phenotype]) -> T.Population:
    population = Population()
    for phenotype in list:
        population.add_genome(Genome(phenotype))
    return population
