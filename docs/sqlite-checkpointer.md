# SQLite Checkpointer

The `SqliteCheckpointer` provides a persistent storage mechanism for tracking evolutionary optimization experiments locally without requiring a dedicated database server.

## Overview

It leverages Python's built-in `sqlite3` module to record generation metadata, fitness metrics, and operation logs. It ensures that you can halt the engine, inspect historical data, and theoretically resume processes from saved checkpoints.

## Database Schema

The database uses a clean, normalized relational schema composed of three main tables:

1. **`experiments`**: Tracks overarching experiment details (name, timestamp).
2. **`iterations`**: Logs metrics for each completed iteration, including population fitness extremes (best, worst) and current population size.
3. **`operations`**: Stores telemetry related to individual phase actions (e.g., reproduction, mutation) alongside execution duration.

### JSON Payload Integration

In addition to relational columns, some tables utilize TEXT columns to store serialized `JSON` payloads. This provides flexibility when storing heterogeneous phenotype data or dynamically changing operational metrics without requiring complex database migrations.

## Usage

To use the checkpointer, instantiate it and attach it to your engine's workflow:

```python
from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer

# Initialize with a local db file path
db = SqliteCheckpointer(db_path="experiments.db")

# Automatically sets up tables on first run
await db.setup()

# Save iteration state
await db.save_iteration(experiment_id=1, iteration_metadata=metadata)
```
