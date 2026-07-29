from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from genai_opt.optimizer_engine.checkpointer.checkpointer import Checkpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class SqliteCheckpointer(Checkpointer[P, Inv]):
    """Persists engine state to a SQLite database between iterations.

    Genomes and metadata are stored as JSON payloads inside a relational table,
    allowing easy retrieval of the latest state or full history per experiment.
    """

    def __init__(
        self,
        db_path: str | Path,
        experiment_id: str = "default",
        *,
        restore_context: dict[str, Any] | None = None,
    ):
        self.db_path = str(db_path)
        self.experiment_id = experiment_id
        self._restore_context = restore_context or {}
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def save_checkpoint(
        self,
        state: EngineState[P, Inv],
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        payload = {
            "iteration": state.iteration,
            "phase": state.phase.value,
            "population": state.population.to_json(),
            "offspring_population": (
                state.offspring_population.to_json() if state.offspring_population is not None else None
            ),
        }
        meta = self._metadata_to_dict(iteration_metadata)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (experiment_id, iteration, phase, payload, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.experiment_id,
                    state.iteration,
                    state.phase.value,
                    json.dumps(payload),
                    json.dumps(meta),
                ),
            )
            conn.commit()

    def load(self, **context: Any) -> EngineState[P, Inv] | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT payload FROM checkpoints
                WHERE experiment_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (self.experiment_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        payload = json.loads(row[0])

        if not isinstance(payload, dict):
            raise ValueError(f"Unrecognized checkpoint format in DB {self.db_path}")

        iteration = payload.get("iteration")
        genomes = payload.get("population", payload.get("genomes"))
        if not isinstance(iteration, int) or not isinstance(genomes, list):
            raise ValueError(f"Unrecognized checkpoint format in DB {self.db_path}")

        restore_context = {**self._restore_context, **context}
        population = Population.from_json(genomes, **restore_context)

        phase_value = payload.get("phase", IterationPhase.EVALUATE_POPULATION.value)
        try:
            phase = IterationPhase(phase_value)
        except ValueError as error:
            raise ValueError(f"Unrecognized checkpoint phase in DB {self.db_path}: {phase_value!r}") from error

        offspring_data = payload.get("offspring_population")
        if offspring_data is not None and not isinstance(offspring_data, list):
            raise ValueError(f"Unrecognized offspring population in DB {self.db_path}")

        offspring_population = (
            Population.from_json(offspring_data, **restore_context) if offspring_data is not None else None
        )

        return EngineState(
            population=population,
            iteration=iteration,
            phase=phase,
            offspring_population=offspring_population,
        )

    def _metadata_to_dict(self, iteration_metadata: IterationMetadata[P, Inv]) -> dict[str, Any]:
        fitnesses = [state.fitness for state in iteration_metadata.phenotype_states if state.fitness is not None]
        return {
            "iteration": iteration_metadata.iteration,
            "phase": iteration_metadata.phase.value if iteration_metadata.phase is not None else None,
            "population_size": len(iteration_metadata.phenotype_states),
            "best_fitness": max(fitnesses) if fitnesses else None,
            "worst_fitness": min(fitnesses) if fitnesses else None,
            "mean_fitness": (sum(fitnesses) / len(fitnesses)) if fitnesses else None,
            "total_tokens": iteration_metadata.total_tokens,
            "total_cost": iteration_metadata.total_cost,
            "total_duration_seconds": iteration_metadata.total_duration_seconds,
            "operations": [self._operation_to_dict(operation) for operation in iteration_metadata.operations],
        }

    @staticmethod
    def _operation_to_dict(operation: Operation) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": str(operation.id),
            "kind": operation.kind,
            "duration_seconds": operation.duration_seconds,
            "tokens": operation.tokens,
            "cost": operation.cost,
        }
        if operation.llm_metadata is not None:
            data["model"] = operation.llm_metadata.model
            data["tokens_in"] = operation.llm_metadata.tokens_in
            data["tokens_out"] = operation.llm_metadata.tokens_out
        return data
