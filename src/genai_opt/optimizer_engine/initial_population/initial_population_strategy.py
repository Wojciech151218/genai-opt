from __future__ import annotations

from genai_opt.optimizer_engine.population import Population
from typing import TypeVar
from genai_opt.optimizer_engine.genome import Genome
INVOCATION = TypeVar('INVOCATION')
PHENOTYPE = TypeVar('PHENOTYPE')    

def initial_Population_from_list(list: list[PHENOTYPE]) -> Population[PHENOTYPE,INVOCATION]:
    population = Population()
    for phenotype in list:
        population.add_genome(Genome(phenotype))
    return population