"""Tests for IterationMetadata."""

import asyncio

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.iteration_metadata import (
    IterationMetadata,
    PhenotypeState,
)
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population


def test_iteration_metadata_from_population():
    pop = Population()
    pop.add_genome(FloatGenome(50.0, target=50.0))
    operations = asyncio.run(pop.evaluate_population())

    metadata = IterationMetadata.from_population(
        iteration=2,
        population=pop,
        operations=operations,
    )

    assert metadata.iteration == 2
    assert len(metadata.phenotype_states) == 1
    assert metadata.phenotype_states[0].fitness == 100.0
    assert metadata.phenotype_states[0].invocation == 50.0
    assert len(metadata.operations) == 2
    assert {operation.kind for operation in metadata.operations} == {"invoke", "evaluate"}


def test_iteration_metadata_totals():
    metadata = IterationMetadata(
        iteration=0,
        phenotype_states=[PhenotypeState(phenotype=1.0, fitness=10.0, invocation=1.0)],
        operations=[
            Operation(1.0, kind="invoke", duration_seconds=0.5, tokens_in=6, tokens_out=4),
            Operation(10.0, kind="evaluate", duration_seconds=0.25, tokens_in=3, tokens_out=2),
        ],
    )

    assert metadata.total_tokens == 15
    assert metadata.total_duration_seconds == 0.75
    assert metadata.tokens_by_kind("invoke") == 10
    assert metadata.duration_by_kind("evaluate") == 0.25
