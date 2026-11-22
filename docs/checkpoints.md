# Checkpoints and Resuming

A checkpoint lets an interrupted run continue instead of starting over. For a
float experiment that saves seconds; for an LLM-backed experiment it is the
difference between resuming and paying for a whole generation twice.

## Enabling checkpoints

Pass a `checkpointer` to `ExperimentBuilder`, then run
`builder.build().from_checkpoint().run()`. The checkpointer saves after each
completed phase. Work in a phase that was interrupted before its save may run
again.

| Backend | What it keeps |
| --- | --- |
| `FilesystemCheckpointer(directory)` | The latest state and its phase summary as JSON files. |
| [`SqliteCheckpointer(db_path, experiment_id)`](sqlite-checkpointer.md) | A history of phase checkpoints grouped by experiment ID. |
| No checkpointer | Nothing is saved or restored. |

`from_checkpoint()` is safe on a first run. When no checkpoint exists it returns
the engine unchanged, so one code path covers both starting and resuming. The
numeric demo already does this with SQLite. Once the saved iteration limit is
reached, calling it again with the same limit returns the saved population.
Pass `checkpoint_db=None` for a fresh, unsaved run. Use a new path or a
different experiment ID to keep independent persisted runs separate.

## Filesystem Checkpoints

The checkpoint directory holds two files, both rewritten on every save.

`checkpoint.json` is the state needed to resume:

- `iteration` — completed iterations so far
- `phase` — the next phase to execute
- `population` — every genome, serialized by its own `to_json()`
- `offspring_population` — present only between the reproduce and replace phases

`checkpoint_meta.json` is a human-readable summary of the phase that just
finished: population size, best, worst and mean fitness, total tokens, cost,
duration, and a per-operation breakdown. Nothing reads it back; it is there for
you.

Only the latest checkpoint is kept. Each file is written to a temporary file
and then replaced. An interruption between the two replacements can leave the
summary behind the state. Use SQLite if you need the history of completed phases.

## Restore context

Checkpoints are JSON, so anything that is not JSON cannot go in them. For a
`FloatGenome` that is not a problem. For an LLM-backed genome the prompt text,
the model description and the invocation schema's import path are stored, but the
chat model itself and the invoke, evaluate, mutate and crossover closures are not.

Supply these collaborators again on load. The haiku builder, for example,
passes `haiku_checkpoint_restore_context(llm, task_message)` to
`FilesystemCheckpointer(restore_context=...)`.

For a custom `Genome`, keep the class in an importable module. Extend
`to_json()` if you need to store fields beyond the base payload, and implement
`_from_json()` to rebuild the instance and call `_restore_runtime_state()`.

Anything passed to `from_checkpoint(**context)` is merged over the context given
to the constructor, so you can override individual entries at load time. A
missing operation function raises `ValueError` naming exactly what was absent.

Credentials are deliberately excluded from `llm_to_config`, so a checkpoint never
serializes an API key through that helper. The key comes from the environment
when the model is rebuilt, or from an explicit `api_key` entry in the restore
context. Do not put credentials into your own serialized data.

## What invalidates a checkpoint

Because types are recorded as import paths and invocations as validated JSON, some
edits make an existing checkpoint unreadable:

- **Renaming or moving a genome class or invocation schema.** The stored import
  path no longer resolves, and loading raises `ValueError` for an unknown genome
  type or `ModuleNotFoundError` for a missing module.
- **Changing an invocation schema incompatibly.** Stored invocations are validated
  against the schema on load, so a removed or retyped required field raises a
  pydantic `ValidationError`.
- **Removing or renaming an `IterationPhase` value.** Loading raises `ValueError`
  for an unrecognized phase.

These fail loudly on purpose. Silently discarding a checkpoint would quietly
restart a run you have already paid for. When a checkpoint is genuinely obsolete,
use a new location or archive the old data before starting over.
