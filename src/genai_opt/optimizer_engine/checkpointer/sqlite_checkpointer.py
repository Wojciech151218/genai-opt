from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from genai_opt.optimizer_engine.checkpointer.checkpointer import Checkpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class OperationRecord(BaseModel):
    id: str
    kind: str
    duration_seconds: float
    tokens: int
    cost: float
    model_name: str | None = Field(default=None, alias="model")
    tokens_in: int | None = None
    tokens_out: int | None = None


class IterationMetadataRecord(BaseModel):
    iteration: int
    phase: str | None
    population_size: int
    best_fitness: float | None
    worst_fitness: float | None
    mean_fitness: float | None
    total_tokens: int
    total_cost: float
    total_duration_seconds: float
    operations: list[OperationRecord]


class CheckpointPayloadRecord(BaseModel):
    iteration: int
    phase: str
    population: list[dict[str, Any]]
    offspring_population: list[dict[str, Any]] | None


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
        payload_record = CheckpointPayloadRecord(
            iteration=state.iteration,
            phase=state.phase.value,
            population=state.population.to_json(),
            offspring_population=state.offspring_population.to_json()
            if state.offspring_population is not None
            else None,
        )
        meta_record = self._metadata_to_record(iteration_metadata)

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
                    payload_record.model_dump_json(),
                    meta_record.model_dump_json(by_alias=True),
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

        payload_record = CheckpointPayloadRecord.model_validate_json(row[0])

        restore_context = {**self._restore_context, **context}
        population = Population.from_json(payload_record.population, **restore_context)

        try:
            phase = IterationPhase(payload_record.phase)
        except ValueError as error:
            raise ValueError(f"Unrecognized checkpoint phase in DB {self.db_path}: {payload_record.phase!r}") from error

        offspring_population = (
            Population.from_json(payload_record.offspring_population, **restore_context)
            if payload_record.offspring_population is not None
            else None
        )

        return EngineState(
            population=population,
            iteration=payload_record.iteration,
            phase=phase,
            offspring_population=offspring_population,
        )

    def _metadata_to_record(self, iteration_metadata: IterationMetadata[P, Inv]) -> IterationMetadataRecord:
        fitnesses = [state.fitness for state in iteration_metadata.phenotype_states if state.fitness is not None]
        return IterationMetadataRecord(
            iteration=iteration_metadata.iteration,
            phase=iteration_metadata.phase.value if iteration_metadata.phase is not None else None,
            population_size=len(iteration_metadata.phenotype_states),
            best_fitness=max(fitnesses) if fitnesses else None,
            worst_fitness=min(fitnesses) if fitnesses else None,
            mean_fitness=(sum(fitnesses) / len(fitnesses)) if fitnesses else None,
            total_tokens=iteration_metadata.total_tokens,
            total_cost=iteration_metadata.total_cost,
            total_duration_seconds=iteration_metadata.total_duration_seconds,
            operations=[self._operation_to_record(operation) for operation in iteration_metadata.operations],
        )

    @staticmethod
    def _operation_to_record(operation: Operation) -> OperationRecord:
        return OperationRecord(
            id=str(operation.id),
            kind=operation.kind,
            duration_seconds=operation.duration_seconds,
            tokens=operation.tokens,
            cost=operation.cost,
            model=operation.llm_metadata.model if operation.llm_metadata else None,
            tokens_in=operation.llm_metadata.tokens_in if operation.llm_metadata else None,
            tokens_out=operation.llm_metadata.tokens_out if operation.llm_metadata else None,
        )
