"""Runnable example experiments.

:mod:`~genai_opt.experiments.simple_experiment` needs no credentials and evolves
a float toward a target, which makes it the quickest way to see the engine work.
:mod:`~genai_opt.experiments.haiku_experiment` evolves a system prompt and does
call a real LLM. Its names are re-exported lazily here so that importing this
package never pulls in the LLM stack unless you ask for them.
"""

from genai_opt.experiments.float_genome import FloatGenome

__all__ = [
    "FloatGenome",
    "HaikuEvaluation",
    "HaikuOutput",
    "build_haiku_experiment",
    "create_initial_population",
    "run_haiku_experiment",
]


def __getattr__(name: str):
    if name in {
        "HaikuEvaluation",
        "HaikuOutput",
        "build_haiku_experiment",
        "create_initial_population",
        "run_haiku_experiment",
    }:
        from genai_opt.experiments import haiku_experiment

        return getattr(haiku_experiment, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
