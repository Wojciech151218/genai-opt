"""Runnable example experiments.

``simple_experiment`` needs no credentials and evolves a float toward a target.
``haiku_experiment`` evolves a system prompt and does call a real LLM. Its names
are re-exported lazily here so that importing this package never pulls in the
LLM stack unless you ask for them.
"""

from experiments.float_genome import FloatGenome

__all__ = [
    "FloatGenome",
    "HaikuEvaluation",
    "HaikuOutput",
    "build_haiku_experiment",
    "create_initial_population",
    "haiku_checkpoint_restore_context",
    "run_haiku_experiment",
]


def __getattr__(name: str):
    if name in {
        "HaikuEvaluation",
        "HaikuOutput",
        "build_haiku_experiment",
        "create_initial_population",
        "haiku_checkpoint_restore_context",
        "run_haiku_experiment",
    }:
        from experiments import haiku_experiment

        return getattr(haiku_experiment, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
