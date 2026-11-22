# SQLite Checkpointer

`SqliteCheckpointer` stores engine state and phase metadata in a local SQLite
database. Use it to resume a run or inspect its history without setting up a
database server.

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

## Basic Usage

```python
from pathlib import Path
from uuid import uuid4

from experiments.simple_experiment import build_simple_experiment
from genai_opt.optimizer_engine import SqliteCheckpointer


db_path: Path = Path(".checkpoints/numeric-tutorial.db")
experiment_id: str = f"numeric-{uuid4().hex}"
for limit in (1, 2):
    engine = build_simple_experiment(
        iterations=limit,
        checkpoint_db=db_path,
        experiment_id=experiment_id,
        websocket_port=0,
    ).build().from_checkpoint()
    engine.run()
    print(engine.iteration)
    #> 1 (first run), 2 (second run)

reader = SqliteCheckpointer[float, float](db_path, experiment_id)
checkpoints = reader.list_checkpoints()
print(len(checkpoints))
#> 10
```

Run this example from a source checkout. Both runs share an experiment ID, so
the second resumes after iteration one. Five phases per iteration produce ten
records in total. Running the script again creates a new experiment ID in the
same local database, so its records stay separate.

## Configuration

| Parameter | Default | Effect |
| --- | --- | --- |
| `db_path` | Required | Path to a persistent SQLite file. |
| `experiment_id` | `"default"` | Selects the run to save or restore in that file. |
| `genome` | `None` | Optional template that supplies operation functions to restore compatible genomes. |

For your own experiment, pass a `SqliteCheckpointer` as the builder's
`checkpointer`. Use `list_experiments()`, `list_checkpoints()`, and
`get_checkpoint(id)` to inspect history. A missing ID returns `None`; an
experiment without checkpoints has an empty list.
