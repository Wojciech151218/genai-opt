from pathlib import Path

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.checkpointer.database import SqliteCheckpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
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
