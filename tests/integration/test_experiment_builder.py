from pathlib import Path

from experiments.float_genome import FloatGenome
from experiments.simple_experiment import build_simple_experiment, run_simple_experiment

from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer
from genai_opt.optimizer_engine.convergence_criterion import iteration_limited_convergence
from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.experiment_builder import ExperimentBuilder
from genai_opt.optimizer_engine.experiment_controller.websocket_controller import WebSocketExperimentController
from genai_opt.optimizer_engine.mutation_policy import random_mutation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy import ReproductionPolicy, generational_reproduction
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import tournament_selection


def test_experiment_builder_builds_engine():
    """build_simple_experiment().build() should return an Engine instance."""
    engine = build_simple_experiment().build()
    assert isinstance(engine, Engine), f"Expected Engine, got {type(engine).__name__}"
    assert isinstance(engine.experiment_controller, WebSocketExperimentController)
    assert engine.reuse_evaluations is False


def test_experiment_builder_passes_reuse_evaluations_to_engine():
    builder = ExperimentBuilder(
        inital_population_strategy=lambda: Population([FloatGenome(1.0)]),
        convergence_criterion=iteration_limited_convergence(1),
        mutation_policy=random_mutation(0.0),
        reproduction_policy=ReproductionPolicy(generational_reproduction(1), tournament_selection),
        reuse_evaluations=True,
    )
    assert builder.build().reuse_evaluations is True


def test_simple_experiment_uses_sqlite_checkpointer(tmp_path: Path):
    engine = build_simple_experiment(checkpoint_db=tmp_path / "simple.db").build()
    assert isinstance(engine.checkpointer, SqliteCheckpointer)
    assert engine.checkpointer.experiment_id == "simple_experiment"


def test_simple_experiment_exposes_reuse_evaluations():
    engine = build_simple_experiment(reuse_evaluations=True).build()
    assert engine.reuse_evaluations is True


def test_simple_experiment_persists_to_sqlite(tmp_path: Path):
    db_path = tmp_path / "run.db"
    run_simple_experiment(
        iterations=1,
        population_size=4,
        checkpoint_db=db_path,
    )
    loaded = SqliteCheckpointer(db_path=db_path, experiment_id="simple_experiment").load()
    assert loaded is not None
    assert loaded.iteration == 1
