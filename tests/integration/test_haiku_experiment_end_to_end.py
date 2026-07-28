"""End-to-end runs of the LLM-backed experiment against a scripted chat model.

Everything here exercises the paths that only run when a real provider is
involved: structured output, token accounting, mutation actually replacing a
prompt, and checkpoint round-trips of a genome whose collaborators cannot be
serialized. None of it touches the network.
"""

import asyncio

import pytest
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage

from fakes import MALFORMED_HAIKU, FakeChatModel
from genai_opt.adapters.simple_system_prompt_genome.types import SimpleSystemPromptPhenotype
from genai_opt.experiments.haiku_experiment import (
    SEED_SYSTEM_PROMPTS,
    HaikuOutput,
    build_haiku_experiment,
    build_haiku_task_message,
    create_initial_population,
    haiku_checkpoint_restore_context,
)
from genai_opt.optimizer_engine.checkpointer import FilesystemCheckpointer
from genai_opt.optimizer_engine.engine_state import IterationPhase


def test_full_run_evaluates_every_genome_and_records_usage() -> None:
    llm = FakeChatModel()
    engine = build_haiku_experiment(
        llm,
        iterations=2,
        population_size=3,
        mutation_rate=1.0,
        shared_task=build_haiku_task_message("hanami"),
    ).build()

    population = engine.run()

    assert engine.iteration == 2
    assert population.get_genome_count() == 3
    for genome in population.population:
        assert genome.evaluation > 0
        assert genome.invocation is not None

    assert set(llm.requested_schemas) == {"HaikuOutput", "HaikuEvaluation", "SystemPromptMutation"}


def test_every_phase_reports_its_operations() -> None:
    """Each phase must report operations, since that is what drives cost tracking."""
    llm = FakeChatModel()
    engine = build_haiku_experiment(
        llm,
        iterations=1,
        population_size=2,
        mutation_rate=1.0,
    ).build()

    async def collect() -> dict[IterationPhase, int]:
        tokens: dict[IterationPhase, int] = {}
        for _ in range(5):
            metadata = await engine.step()
            assert metadata.phase is not None
            tokens[metadata.phase] = metadata.total_tokens
        return tokens

    tokens_by_phase = asyncio.run(collect())

    assert tokens_by_phase[IterationPhase.EVALUATE_POPULATION] > 0
    assert tokens_by_phase[IterationPhase.REPRODUCE] > 0
    assert tokens_by_phase[IterationPhase.MUTATE] > 0
    assert tokens_by_phase[IterationPhase.EVALUATE_OFFSPRING] > 0
    assert tokens_by_phase[IterationPhase.REPLACE] == 0


def test_mutation_replaces_the_evolved_prompt() -> None:
    """A run that always mutates must not end on the seed prompts."""
    llm = FakeChatModel()
    engine = build_haiku_experiment(
        llm,
        iterations=1,
        population_size=2,
        mutation_rate=1.0,
    ).build()

    population = engine.run()

    evolved = {str(genome.phenotype.system_prompt) for genome in population.population}
    assert evolved.isdisjoint({str(prompt) for prompt in SEED_SYSTEM_PROMPTS})


def test_malformed_haiku_scores_zero_without_calling_the_judge() -> None:
    """Form is checked in code, so a bad poem must not spend a judging call."""
    llm = FakeChatModel(replies={HaikuOutput: MALFORMED_HAIKU})
    engine = build_haiku_experiment(llm, iterations=1, population_size=2).build()

    population = engine.run()

    assert [genome.evaluation for genome in population.population] == [0.0, 0.0]
    assert "HaikuEvaluation" not in llm.requested_schemas


def test_structured_output_parse_failure_propagates() -> None:
    """A reply the schema cannot parse must fail the run, not score as zero."""
    llm = FakeChatModel(parsing_error=OutputParserException("model returned prose, not JSON"))
    engine = build_haiku_experiment(llm, iterations=1, population_size=2).build()

    with pytest.raises(OutputParserException, match="model returned prose"):
        engine.run()


def test_checkpoint_round_trip_restores_the_evolved_prompts(tmp_path) -> None:
    """Prompts survive a checkpoint even though the operation functions cannot."""
    llm = FakeChatModel()
    task = build_haiku_task_message("hanami")
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(
        tmp_path,
        restore_context=haiku_checkpoint_restore_context(llm, task),
    )
    engine = build_haiku_experiment(
        llm,
        iterations=1,
        population_size=2,
        mutation_rate=1.0,
        shared_task=task,
    ).build()
    engine.checkpointer = checkpointer

    engine.run()
    original_prompts = [str(genome.phenotype.system_prompt) for genome in engine.population.population]

    resumed = build_haiku_experiment(
        llm,
        iterations=1,
        population_size=2,
        shared_task=task,
    ).build()
    resumed.checkpointer = checkpointer
    resumed.from_checkpoint()

    restored_prompts = [str(genome.phenotype.system_prompt) for genome in resumed.population.population]
    assert restored_prompts == original_prompts
    assert resumed.iteration == 1


def test_checkpoint_stores_no_credentials(tmp_path) -> None:
    """An API key must never reach disk, whatever else a checkpoint holds."""
    llm = FakeChatModel(model="fake-model")
    task = build_haiku_task_message("hanami")
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)
    engine = build_haiku_experiment(llm, iterations=1, population_size=2, shared_task=task).build()
    engine.checkpointer = checkpointer

    engine.run()

    written = (tmp_path / "checkpoint.json").read_text()
    assert "fake-model" in written
    for secret_marker in ("api_key", "openai_api_key", "sk-"):
        assert secret_marker not in written.lower()


def test_population_seeds_are_reused_when_population_exceeds_seeds() -> None:
    llm = FakeChatModel()
    population = create_initial_population(llm, population_size=len(SEED_SYSTEM_PROMPTS) + 2)

    prompts = [genome.phenotype.system_prompt for genome in population.population]
    assert prompts[: len(SEED_SYSTEM_PROMPTS)] == list(SEED_SYSTEM_PROMPTS)
    assert prompts[len(SEED_SYSTEM_PROMPTS)] == SEED_SYSTEM_PROMPTS[0]


def test_phenotype_accepts_the_fake_model() -> None:
    """Guards the fake itself: the phenotype validates its llm field."""
    phenotype = SimpleSystemPromptPhenotype(system_prompt="write a haiku", llm=FakeChatModel())

    assert isinstance(phenotype.llm, FakeChatModel)


def test_task_message_is_shared_across_the_population() -> None:
    """Genomes must answer the same question, or their scores are not comparable."""
    llm = FakeChatModel()
    task = HumanMessage(content="Write a haiku about hanami.")
    population = create_initial_population(llm, population_size=3, shared_task=task)

    assert population.get_genome_count() == 3
    assert {str(genome.phenotype.system_prompt) for genome in population.population}
