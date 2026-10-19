from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from genai_opt.adapters.simple_system_prompt_genome import (
    SimpleSystemPromptGenome,
    SimpleSystemPromptPhenotype,
    crossover_prompt_function,
    invoke_task_message_function,
    mutate_prompt_function,
)
from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.experiments.haiku_experiment import HaikuOutput, evaluate_haiku_function
from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.population import Population


class _StubChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "stub"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError


def test_sqlite_checkpointer_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    checkpointer = SqliteCheckpointer(db_path=db_path, experiment_id="test_exp")

    # Arrange
    genomes = [FloatGenome(phenotype=float(v), target=50.0) for v in range(3)]
    for g in genomes:
        g._set_evaluation(100.0 - abs(g.phenotype - 50.0))
    population = Population(genomes)

    offspring_genomes = [FloatGenome(phenotype=10.0, target=50.0)]
    for g in offspring_genomes:
        g._set_evaluation(60.0)
    offspring_population = Population(offspring_genomes)

    state = EngineState(
        population=population,
        iteration=42,
        phase=IterationPhase.MUTATE,
        offspring_population=offspring_population,
    )
    metadata = IterationMetadata(iteration=42)
    metadata.phase = IterationPhase.MUTATE

    # Act
    checkpointer.save_checkpoint(state, metadata)
    loaded_state = checkpointer.load()

    # Assert
    assert loaded_state is not None
    assert loaded_state.iteration == 42
    assert loaded_state.phase == IterationPhase.MUTATE
    assert loaded_state.population.get_genome_count() == 3
    assert loaded_state.population.population[0].phenotype == 0.0
    assert loaded_state.population.population[0].evaluation == 50.0

    assert loaded_state.offspring_population is not None
    assert loaded_state.offspring_population.get_genome_count() == 1
    assert loaded_state.offspring_population.population[0].phenotype == 10.0
    assert loaded_state.offspring_population.population[0].evaluation == 60.0


def test_sqlite_checkpointer_empty_returns_none(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    checkpointer = SqliteCheckpointer(db_path=db_path)
    loaded_state = checkpointer.load()
    assert loaded_state is None


def test_sqlite_checkpointer_extracts_restore_context_from_genome(tmp_path: Path) -> None:
    llm = _StubChatModel()
    task = HumanMessage(content="Write a haiku.")
    invoke = invoke_task_message_function(task, HaikuOutput)
    evaluate = evaluate_haiku_function(llm)
    mutate = mutate_prompt_function("Mutate: {system_prompt}", llm)
    crossover = crossover_prompt_function("A: {prompt_a} B: {prompt_b}", llm)
    genome = SimpleSystemPromptGenome(
        phenotype=SimpleSystemPromptPhenotype(system_prompt="You are a poet.", llm=llm),
        invocation_schema=HaikuOutput,
        invoke_function=invoke,
        evaluate_function=evaluate,
        mutate_function=mutate,
        crossover_function=crossover,
    )

    checkpointer = SqliteCheckpointer(db_path=tmp_path / "haiku.db", genome=genome)

    assert checkpointer._restore_context == {
        "invocation_schema": HaikuOutput,
        "invoke_function": invoke,
        "evaluate_function": evaluate,
        "mutate_function": mutate,
        "crossover_function": crossover,
    }
    assert "llm" not in checkpointer._restore_context


def test_sqlite_checkpointer_memory_db() -> None:
    # A memory database will be erased upon connection close unless connection is shared,
    # but since our Checkpointer opens/closes connection on each method call,
    # :memory: will not work across calls unless we keep a connection alive.
    # We will test normal file based sqlite checkpointer for reliable disk persistence.
    pass
