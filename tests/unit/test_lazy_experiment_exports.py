"""The experiments package re-exports its LLM-backed names lazily.

Importing ``genai_opt.experiments`` must not drag in the LLM stack, or the
credential-free experiment stops being credential-free.
"""

import subprocess
import sys

import pytest

import genai_opt.experiments as experiments


def test_lazy_names_resolve_to_the_haiku_module() -> None:
    from genai_opt.experiments import haiku_experiment

    for name in ("HaikuOutput", "HaikuEvaluation", "build_haiku_experiment", "run_haiku_experiment"):
        assert getattr(experiments, name) is getattr(haiku_experiment, name)


def test_eager_names_are_still_available_directly() -> None:
    from genai_opt.experiments.float_genome import FloatGenome

    assert experiments.FloatGenome is FloatGenome


def test_unknown_attribute_raises_attribute_error() -> None:
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
        getattr(experiments, "nonexistent")  # noqa: B009


def test_every_advertised_name_is_reachable() -> None:
    """``__all__`` and the lazy dispatch table must not drift apart."""
    for name in experiments.__all__:
        assert getattr(experiments, name) is not None


def test_importing_the_package_does_not_import_the_haiku_module() -> None:
    program = """
import sys

import genai_opt.experiments

assert "genai_opt.experiments.haiku_experiment" not in sys.modules, "haiku module imported eagerly"
genai_opt.experiments.HaikuOutput
assert "genai_opt.experiments.haiku_experiment" in sys.modules, "lazy access did not import it"
print("lazy")
"""
    result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert "lazy" in result.stdout
