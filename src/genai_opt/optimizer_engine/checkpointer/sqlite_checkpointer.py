from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from genai_opt.optimizer_engine.checkpointer.checkpointer import Checkpointer
from genai_opt.optimizer_engine.engine_state import EngineState, IterationPhase
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P

_RESTORE_ATTRS = (
    "invocation_schema",
    "invoke_function",
    "evaluate_function",
    "mutate_function",
    "crossover_function",
)


class OperationRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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


class GenomeSnapshotRecord(BaseModel):
    id: str
    genome_type: str | None = None
    phenotype: Any
    fitness: float | None = None
    invocation: Any = None


class ExperimentSummaryRecord(BaseModel):
    experiment_id: str
    checkpoint_count: int
    latest_iteration: int
    latest_phase: str
    best_fitness: float | None = None
    total_tokens: int = 0
    total_cost: float = 0.0
    last_updated: str


class CheckpointSummaryRecord(BaseModel):
    id: int
    experiment_id: str
    iteration: int
    phase: str
    next_phase: str
    population_size: int
    best_fitness: float | None = None
    worst_fitness: float | None = None
    mean_fitness: float | None = None
    total_tokens: int = 0
    total_cost: float = 0.0
    total_duration_seconds: float = 0.0
    operation_count: int = 0
    timestamp: str


class CheckpointDetailRecord(CheckpointSummaryRecord):
    population: list[GenomeSnapshotRecord]
    offspring_population: list[GenomeSnapshotRecord] | None = None
    operations: list[OperationRecord]


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
        genome: Genome[P, Inv] | None = None,
    ):
        self.db_path = str(db_path)
        self.experiment_id = experiment_id
        self._restore_context: dict[str, Any] = {}
        if genome is not None:
            for attr in _RESTORE_ATTRS:
                value = getattr(genome, f"_{attr}", None)
                if value is not None:
                    self._restore_context[attr] = value
        self._init_db()

    def _init_db(self) -> None:
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
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

    def list_experiments(self) -> list[ExperimentSummaryRecord]:
        """Return summary statistics for every experiment stored in this database."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT experiment_id, iteration, phase, metadata, timestamp
                FROM checkpoints
                ORDER BY id ASC
                """
            ).fetchall()

        grouped: dict[str, dict[str, Any]] = {}
        for exp_id, row_iteration, row_phase, raw_metadata, timestamp in rows:
            meta = IterationMetadataRecord.model_validate_json(raw_metadata)
            completed_phase = meta.phase or row_phase
            entry = grouped.get(exp_id)
            if entry is None:
                entry = {
                    "experiment_id": exp_id,
                    "checkpoint_count": 0,
                    "latest_iteration": meta.iteration if meta.phase is not None else row_iteration,
                    "latest_phase": completed_phase,
                    "best_fitness": None,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "last_updated": timestamp,
                }
                grouped[exp_id] = entry

            entry["checkpoint_count"] += 1
            entry["latest_iteration"] = meta.iteration if meta.phase is not None else row_iteration
            entry["latest_phase"] = completed_phase
            entry["total_tokens"] += meta.total_tokens
            entry["total_cost"] += meta.total_cost
            entry["last_updated"] = timestamp
            if meta.best_fitness is not None and (
                entry["best_fitness"] is None or meta.best_fitness > entry["best_fitness"]
            ):
                entry["best_fitness"] = meta.best_fitness

        return [ExperimentSummaryRecord(**item) for item in reversed(list(grouped.values()))]

    def list_checkpoints(self, experiment_id: str | None = None) -> list[CheckpointSummaryRecord]:
        """Return ordered checkpoint summaries for a given experiment."""
        target_experiment_id = experiment_id if experiment_id is not None else self.experiment_id
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, experiment_id, iteration, phase, metadata, timestamp
                FROM checkpoints
                WHERE experiment_id = ?
                ORDER BY id ASC
                """,
                (target_experiment_id,),
            ).fetchall()

        summaries: list[CheckpointSummaryRecord] = []
        for checkpoint_id, exp_id, row_iteration, row_phase, raw_metadata, timestamp in rows:
            meta = IterationMetadataRecord.model_validate_json(raw_metadata)
            summaries.append(
                CheckpointSummaryRecord(
                    id=checkpoint_id,
                    experiment_id=exp_id,
                    iteration=meta.iteration if meta.phase is not None else row_iteration,
                    phase=meta.phase or row_phase,
                    next_phase=row_phase,
                    population_size=meta.population_size,
                    best_fitness=meta.best_fitness,
                    worst_fitness=meta.worst_fitness,
                    mean_fitness=meta.mean_fitness,
                    total_tokens=meta.total_tokens,
                    total_cost=meta.total_cost,
                    total_duration_seconds=meta.total_duration_seconds,
                    operation_count=len(meta.operations),
                    timestamp=timestamp,
                )
            )
        return summaries

    def get_checkpoint(self, checkpoint_id: int) -> CheckpointDetailRecord | None:
        """Return the full population snapshot and operation log for a specific checkpoint."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, experiment_id, iteration, phase, payload, metadata, timestamp
                FROM checkpoints
                WHERE id = ?
                """,
                (checkpoint_id,),
            ).fetchone()

        if row is None:
            return None

        cp_id, exp_id, row_iteration, row_phase, raw_payload, raw_metadata, timestamp = row
        payload = CheckpointPayloadRecord.model_validate_json(raw_payload)
        meta = IterationMetadataRecord.model_validate_json(raw_metadata)

        population = [self._clean_genome_snapshot(idx, g) for idx, g in enumerate(payload.population)]
        offspring_population = (
            [self._clean_genome_snapshot(idx, g) for idx, g in enumerate(payload.offspring_population)]
            if payload.offspring_population is not None
            else None
        )

        return CheckpointDetailRecord(
            id=cp_id,
            experiment_id=exp_id,
            iteration=meta.iteration if meta.phase is not None else row_iteration,
            phase=meta.phase or row_phase,
            next_phase=row_phase,
            population_size=meta.population_size,
            best_fitness=meta.best_fitness,
            worst_fitness=meta.worst_fitness,
            mean_fitness=meta.mean_fitness,
            total_tokens=meta.total_tokens,
            total_cost=meta.total_cost,
            total_duration_seconds=meta.total_duration_seconds,
            operation_count=len(meta.operations),
            timestamp=timestamp,
            population=population,
            offspring_population=offspring_population,
            operations=meta.operations,
        )

    @staticmethod
    def _clean_genome_snapshot(idx: int, raw: dict[str, Any]) -> GenomeSnapshotRecord:
        phenotype = raw.get("phenotype")
        if isinstance(phenotype, dict) and "llm" in phenotype and "system_prompt" in phenotype:
            phenotype = {k: v for k, v in phenotype.items() if k != "llm"}
        elif phenotype is None and "system_prompt" in raw:
            phenotype = {"system_prompt": raw["system_prompt"]}

        return GenomeSnapshotRecord(
            id=f"genome_{idx + 1}",
            genome_type=raw.get("genome_type"),
            phenotype=phenotype,
            fitness=raw.get("evaluation"),
            invocation=raw.get("invocation"),
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
