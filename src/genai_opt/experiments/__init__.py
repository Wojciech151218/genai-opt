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
