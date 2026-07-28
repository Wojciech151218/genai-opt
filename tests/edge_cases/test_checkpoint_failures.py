"""How bad checkpoints and missing credentials fail.

The rule these tests pin down is that a checkpoint the engine cannot understand
must fail loudly. Treating it as "no checkpoint" would silently restart a run
that has already been paid for.
"""

import json

import pytest

from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine.checkpointer import FilesystemCheckpointer
from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import (
    iteration_limited_convergence,
)
from genai_opt.optimizer_engine.engine import Engine
from genai_opt.optimizer_engine.mutation_policy.mutation_policy import random_mutation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.reproduction_policy.parent_selection import tournament_selection
from genai_opt.optimizer_engine.reproduction_policy.reproduction_policy import ReproductionPolicy
from genai_opt.optimizer_engine.reproduction_policy.reproduction_strategy import (
    generational_reproduction,
)


def _build_engine(checkpointer: FilesystemCheckpointer) -> Engine:
    return Engine(
        population=Population([FloatGenome(float(value)) for value in (10.0, 20.0, 30.0)]),
        convergence_criterion=iteration_limited_convergence(1),
        mutation_policy=random_mutation(0.5),
        reproduction_policy=ReproductionPolicy(generational_reproduction(3), tournament_selection),
        checkpointer=checkpointer,
    )


def _write_checkpoint(tmp_path, payload) -> FilesystemCheckpointer:
    (tmp_path / "checkpoint.json").write_text(json.dumps(payload))
    return FilesystemCheckpointer(tmp_path)


def test_missing_checkpoint_directory_starts_a_fresh_run(tmp_path) -> None:
    """A first run and a resumed run must share one code path."""
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path / "does-not-exist")

    engine = _build_engine(checkpointer).from_checkpoint()

    assert engine.iteration == 0
    assert engine.population.get_genome_count() == 3


def test_invalid_json_is_reported_rather_than_ignored(tmp_path) -> None:
    (tmp_path / "checkpoint.json").write_text("{not json at all")
    checkpointer: FilesystemCheckpointer = FilesystemCheckpointer(tmp_path)

    with pytest.raises(json.JSONDecodeError):
        _build_engine(checkpointer).from_checkpoint()


def test_a_payload_that_is_not_an_object_is_rejected(tmp_path) -> None:
    checkpointer = _write_checkpoint(tmp_path, ["not", "a", "checkpoint"])

    with pytest.raises(ValueError, match="Unrecognized checkpoint format"):
        _build_engine(checkpointer).from_checkpoint()


def test_an_unknown_genome_type_is_rejected(tmp_path) -> None:
    """A renamed or moved genome class must not silently lose the population."""
    checkpointer = _write_checkpoint(
        tmp_path,
        {
            "iteration": 2,
            "phase": "reproduce",
            "population": [{"genome_type": "some.removed.module.OldGenome", "phenotype": 1.0}],
        },
    )

    with pytest.raises(ValueError, match="Unknown genome type"):
        _build_engine(checkpointer).from_checkpoint()


def test_a_genome_payload_missing_its_type_is_rejected(tmp_path) -> None:
    checkpointer = _write_checkpoint(
        tmp_path,
        {"iteration": 0, "phase": "reproduce", "population": [{"phenotype": 1.0}]},
    )

    with pytest.raises(ValueError, match="genome_type"):
        _build_engine(checkpointer).from_checkpoint()


def test_a_genome_payload_missing_its_phenotype_is_rejected(tmp_path) -> None:
    """A schema change that drops a required field must not restore silently."""
    checkpointer = _write_checkpoint(
        tmp_path,
        {
            "iteration": 0,
            "phase": "reproduce",
            "population": [{"genome_type": "genai_opt.experiments.float_genome.FloatGenome", "target": 50.0}],
        },
    )

    with pytest.raises(ValueError, match="must include phenotype"):
        _build_engine(checkpointer).from_checkpoint()


def test_an_unknown_phase_name_is_rejected(tmp_path) -> None:
    """A phase this version does not have means the checkpoint is not ours."""
    checkpointer = _write_checkpoint(
        tmp_path,
        {
            "iteration": 1,
            "phase": "transcend_population",
            "population": [
                {
                    "genome_type": "genai_opt.experiments.float_genome.FloatGenome",
                    "phenotype": 1.0,
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="phase"):
        _build_engine(checkpointer).from_checkpoint()


def test_a_non_list_population_is_rejected(tmp_path) -> None:
    checkpointer = _write_checkpoint(
        tmp_path,
        {"iteration": 0, "phase": "reproduce", "population": {"genome": "single"}},
    )

    with pytest.raises(ValueError):
        _build_engine(checkpointer).from_checkpoint()


def test_missing_api_key_fails_before_any_work_is_done(monkeypatch, tmp_path) -> None:
    """Credentials are checked up front, not discovered mid-run."""
    from genai_opt.experiments import haiku_experiment

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(haiku_experiment, "load_project_env", lambda: None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        haiku_experiment.create_llm()


def test_missing_api_key_message_names_the_alternatives(monkeypatch) -> None:
    from genai_opt.experiments import haiku_experiment

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(haiku_experiment, "load_project_env", lambda: None)

    with pytest.raises(RuntimeError) as error:
        haiku_experiment.run_haiku_experiment(iterations=1)

    message = str(error.value)
    assert "api_key" in message
    assert "run_haiku_experiment" in message


def test_an_explicit_api_key_bypasses_the_environment(monkeypatch) -> None:
    from genai_opt.experiments import haiku_experiment

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(haiku_experiment, "load_project_env", lambda: None)
    monkeypatch.setattr(
        haiku_experiment,
        "init_chat_model",
        lambda model, **kwargs: ("built", model, kwargs["api_key"]),
    )

    assert haiku_experiment.create_llm(api_key="test-key") == ("built", haiku_experiment.DEFAULT_MODEL, "test-key")
