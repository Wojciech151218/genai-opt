from pathlib import Path

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import LLMMetadata, Operation
from genai_opt.optimizer_engine.population import Population


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


def test_sqlite_checkpointer_memory_db() -> None:
    # A memory database will be erased upon connection close unless connection is shared,
    # but since our Checkpointer opens/closes connection on each method call,
    # :memory: will not work across calls unless we keep a connection alive.
    # We will test normal file based sqlite checkpointer for reliable disk persistence.
    pass


def test_sqlite_checkpointer_history_queries(tmp_path: Path) -> None:
    db_path = tmp_path / "history.db"
    exp_a = SqliteCheckpointer(db_path=db_path, experiment_id="exp_alpha")
    exp_b = SqliteCheckpointer(db_path=db_path, experiment_id="exp_beta")

    g1 = FloatGenome(phenotype=48.0, target=50.0)
    g1._set_invocation(48.0)
    g1._set_evaluation(98.0)
    g2 = FloatGenome(phenotype=30.0, target=50.0)
    g2._set_invocation(30.0)
    g2._set_evaluation(80.0)
    pop = Population([g1, g2])

    op = Operation(
        value=98.0,
        kind="evaluate",
        duration_seconds=1.25,
        llm_metadata=LLMMetadata(model="gpt-4o-mini", tokens_in=100, tokens_out=20, cost=0.01),
    )

    state_0 = EngineState(population=pop, iteration=0, phase=IterationPhase.REPRODUCE)
    meta_0 = IterationMetadata.from_population(0, pop, [op], IterationPhase.EVALUATE_POPULATION)
    exp_a.save_checkpoint(state_0, meta_0)

    state_1 = EngineState(population=pop, iteration=1, phase=IterationPhase.MUTATE, offspring_population=pop)
    meta_1 = IterationMetadata.from_population(1, pop, [], IterationPhase.REPRODUCE)
    exp_a.save_checkpoint(state_1, meta_1)

    exp_b.save_checkpoint(state_0, meta_0)

    experiments = exp_a.list_experiments()
    assert len(experiments) == 2
    by_id = {e.experiment_id: e for e in experiments}
    assert by_id["exp_alpha"].checkpoint_count == 2
    assert by_id["exp_alpha"].latest_iteration == 1
    assert by_id["exp_alpha"].latest_phase == "reproduce"
    assert by_id["exp_alpha"].best_fitness == 98.0
    assert by_id["exp_alpha"].total_tokens == 120

    checkpoints = exp_a.list_checkpoints("exp_alpha")
    assert len(checkpoints) == 2
    assert checkpoints[0].phase == "evaluate_population"
    assert checkpoints[0].next_phase == "reproduce"
    assert checkpoints[0].operation_count == 1
    assert checkpoints[0].mean_fitness == 89.0

    detail = exp_a.get_checkpoint(checkpoints[0].id)
    assert detail is not None
    assert len(detail.population) == 2
    assert detail.population[0].id == "genome_1"
    assert detail.population[0].phenotype == 48.0
    assert detail.population[0].fitness == 98.0
    assert detail.operations[0].model_name == "gpt-4o-mini"
    assert detail.operations[0].tokens == 120

    assert exp_a.get_checkpoint(99999) is None


def test_clean_genome_snapshot_strips_internal_llm() -> None:
    raw = {
        "genome_type": "SimpleSystemPromptGenome",
        "phenotype": {"system_prompt": "Write haiku", "llm": {"client": "secret"}},
        "evaluation": 180.0,
        "invocation": {"line_one": "a", "line_two": "b", "line_three": "c"},
    }
    cleaned = SqliteCheckpointer._clean_genome_snapshot(0, raw)
    assert cleaned.phenotype == {"system_prompt": "Write haiku"}
    assert cleaned.fitness == 180.0
    assert cleaned.id == "genome_1"
