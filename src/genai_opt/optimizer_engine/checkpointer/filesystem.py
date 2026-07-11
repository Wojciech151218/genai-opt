from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic

from genai_opt.optimizer_engine.checkpointer.checkpointer import Checkpointer
from genai_opt.optimizer_engine.genome import Genome
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population
from genai_opt.optimizer_engine.utils.typevars import Inv, P


@dataclass
class _CheckpointPayload(Generic[P, Inv]):
    iteration: int
    population: Population[P, Inv]


class FilesystemCheckpointer(Checkpointer[P, Inv]):
    """Persists engine state to disk between iterations.

    Genomes are stored as JSON (``checkpoint.json``) via each genome's
    ``to_json`` / ``from_json`` methods. A human-readable JSON summary
    (``checkpoint_meta.json``) records iteration stats and operation metadata.
    """

    def __init__(
        self,
        directory: str | Path,
        *,
        restore_context: dict[str, Any] | None = None,
    ):
        self.directory = Path(directory)
        self._checkpoint_path = self.directory / "checkpoint.json"
        self._metadata_path = self.directory / "checkpoint_meta.json"
        self._restore_context = restore_context or {}

    def save_checkpoint(
        self,
        population: Population[P, Inv],
        iteration: int,
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

        payload = {
            "iteration": iteration,
            "genomes": population.to_json(),
        }

        temp_checkpoint = self._checkpoint_path.with_suffix(".json.tmp")
        with temp_checkpoint.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        temp_checkpoint.replace(self._checkpoint_path)

        meta = self._metadata_to_dict(iteration_metadata)
        temp_metadata = self._metadata_path.with_suffix(".json.tmp")
        with temp_metadata.open("w", encoding="utf-8") as handle:
            json.dump(meta, handle, indent=2)
        temp_metadata.replace(self._metadata_path)

    def load(self, **context: Any) -> tuple[Population[P, Inv], int] | None:
        if not self._checkpoint_path.exists():
            return None

        with self._checkpoint_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError(f"Unrecognized checkpoint format in {self._checkpoint_path}")

        iteration = payload.get("iteration")
        genomes = payload.get("genomes")
        if not isinstance(iteration, int) or not isinstance(genomes, list):
            raise ValueError(f"Unrecognized checkpoint format in {self._checkpoint_path}")

        restore_context = {**self._restore_context, **context}
        population = Population.from_json(genomes, **restore_context)
        return population, iteration

    def _metadata_to_dict(self, iteration_metadata: IterationMetadata[P, Inv]) -> dict[str, Any]:
        fitnesses = [
            state.fitness for state in iteration_metadata.phenotype_states if state.fitness is not None
        ]
        return {
            "iteration": iteration_metadata.iteration,
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
