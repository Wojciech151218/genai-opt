from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from experiments.float_genome import FloatGenome

from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer
from genai_opt.optimizer_engine.dashboard_api import (
    DashboardAPIServer,
    discover_databases,
    resolve_database_path,
)
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import LLMMetadata, Operation
from genai_opt.optimizer_engine.population import Population


def _seed_sample_db(db_path: Path) -> None:
    cp = SqliteCheckpointer(db_path=db_path, experiment_id="demo_exp")
    genome = FloatGenome(phenotype=49.5, target=50.0)
    genome._set_invocation(49.5)
    genome._set_evaluation(99.5)
    pop = Population([genome])
    op = Operation(
        value=99.5,
        kind="evaluate",
        duration_seconds=0.4,
        llm_metadata=LLMMetadata(model="gpt-4o-mini", tokens_in=50, tokens_out=10, cost=0.001),
    )
    state = EngineState(population=pop, iteration=0, phase=IterationPhase.REPRODUCE)
    meta = IterationMetadata.from_population(0, pop, [op], IterationPhase.EVALUATE_POPULATION)
    cp.save_checkpoint(state, meta)


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_discover_and_resolve_databases(tmp_path: Path) -> None:
    checkpoints_dir = tmp_path / ".checkpoints"
    db_file = checkpoints_dir / "sample.db"
    _seed_sample_db(db_file)

    dbs = discover_databases(checkpoints_dir, project_root=tmp_path)
    assert len(dbs) == 1
    assert dbs[0]["name"] == "sample.db"
    assert dbs[0]["path"] == ".checkpoints/sample.db"

    resolved = resolve_database_path("sample.db", checkpoints_dir, project_root=tmp_path)
    assert resolved == db_file.resolve()

    with pytest.raises(FileNotFoundError):
        resolve_database_path("missing.db", checkpoints_dir, project_root=tmp_path)
    assert not (checkpoints_dir / "missing.db").exists()


def test_dashboard_api_endpoints(tmp_path: Path) -> None:
    checkpoints_dir = tmp_path / ".checkpoints"
    db_file = checkpoints_dir / "haiku.db"
    _seed_sample_db(db_file)

    server = DashboardAPIServer(host="127.0.0.1", port=0, checkpoints_dir=checkpoints_dir)
    assert server.start() is True
    base_url = f"http://127.0.0.1:{server.bound_port}"

    try:
        health = _get_json(f"{base_url}/api/health")
        assert health == {"status": "ok"}

        databases = _get_json(f"{base_url}/api/databases")
        assert len(databases["databases"]) == 1
        assert databases["databases"][0]["name"] == "haiku.db"

        experiments = _get_json(f"{base_url}/api/experiments?db=haiku.db")
        assert len(experiments["experiments"]) == 1
        assert experiments["experiments"][0]["experiment_id"] == "demo_exp"
        assert experiments["experiments"][0]["best_fitness"] == 99.5

        checkpoints = _get_json(f"{base_url}/api/checkpoints?db=haiku.db&experiment_id=demo_exp")
        assert len(checkpoints["checkpoints"]) == 1
        cp_id = checkpoints["checkpoints"][0]["id"]

        detail = _get_json(f"{base_url}/api/checkpoints/{cp_id}?db=haiku.db")
        assert detail["id"] == cp_id
        assert detail["population"][0]["fitness"] == 99.5
        assert detail["operations"][0]["model"] == "gpt-4o-mini"

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _get_json(f"{base_url}/api/checkpoints/9999?db=haiku.db")
        assert exc_info.value.code == 404
    finally:
        server.stop()
