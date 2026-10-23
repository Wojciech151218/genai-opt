# SQLite Checkpointer

The `SqliteCheckpointer` provides zero-configuration, persistent local storage for evolutionary optimization experiments using Python's standard-library `sqlite3` module and Pydantic schemas.

## Overview

`SqliteCheckpointer` persists engine state and phase telemetry after every step in `Engine.step()`, enabling:
- **Fault-tolerant resumption** via `engine.from_checkpoint()`,
- **Historical inspection** of populations, offspring, fitness statistics, token usage, and LLM operations via Python methods or the Web Dashboard's **Database Explorer**.

## Database Schema

All checkpoints are stored in a single `checkpoints` table created automatically on initialization:

- `id`: Auto-incrementing primary key ordering every recorded phase step.
- `experiment_id`: Logical identifier grouping runs within the same `.db` file.
- `iteration`: Current iteration index.
- `phase`: Next `IterationPhase` to execute upon resumption.
- `payload`: Serialized `CheckpointPayloadRecord` JSON containing `population` and `offspring_population`.
- `metadata`: Serialized `IterationMetadataRecord` JSON containing completed phase metrics (`best_fitness`, `mean_fitness`, `worst_fitness`, `total_tokens`, `total_cost`, `total_duration_seconds`) and `operations`.
- `timestamp`: UTC creation timestamp.

## Usage

### Saving and Resuming Engine State

```python
from genai_opt.optimizer_engine import SqliteCheckpointer

checkpointer = SqliteCheckpointer(
    db_path=".checkpoints/haiku_experiment.db",
    experiment_id="haiku_experiment",
)

# Attach to ExperimentBuilder and restore latest state if present
engine = builder.build().from_checkpoint()
await engine.run()
```

### Querying Historical Runs

`SqliteCheckpointer` also exposes read-only query helpers used by the Database Explorer API:

```python
reader = SqliteCheckpointer(db_path=".checkpoints/haiku_experiment.db")

experiments = reader.list_experiments()
checkpoints = reader.list_checkpoints("haiku_experiment")
detail = reader.get_checkpoint(checkpoints[-1].id)
```
