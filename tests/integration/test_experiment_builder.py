from genai_opt.experiments.simple_experiment import build_simple_experiment
from genai_opt.optimizer_engine.engine import Engine


def test_experiment_builder_builds_engine():
    """build_simple_experiment().build() should return an Engine instance."""
    engine = build_simple_experiment().build()
    assert isinstance(engine, Engine), f"Expected Engine, got {type(engine).__name__}"
