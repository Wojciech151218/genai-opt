# Checkpoints and Resuming

A checkpoint lets an interrupted run continue instead of starting over. For a
float experiment that saves seconds; for an LLM-backed experiment it is the
difference between resuming and paying for a whole generation twice.

## Enabling checkpoints

Pass a `FilesystemCheckpointer` when building the experiment, then chain
`from_checkpoint()` onto the engine:

```python
from genai_opt.optimizer_engine import FilesystemCheckpointer

engine = builder.build().from_checkpoint()
```

`from_checkpoint()` is safe on a first run. When no checkpoint exists it returns
the engine unchanged, so one code path covers both starting and resuming. The
bundled experiments already do this, which is why calling `run_simple_experiment()`
twice continues the earlier run rather than starting fresh. Pass
`checkpoint_dir=None` when you want a self-contained run.

## What is on disk

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

Only the latest checkpoint is kept. Each save writes to a temporary file and
renames it into place, so an interrupted write cannot leave a corrupt checkpoint
behind. Keeping history is up to you — copy the directory between runs.

## Restore context

Checkpoints are JSON, so anything that is not JSON cannot go in them. For a
`FloatGenome` that is not a problem. For an LLM-backed genome the prompt text,
the model description and the invocation schema's import path are stored, but the
chat model itself and the invoke, evaluate, mutate and crossover closures are not.

Those have to be supplied again on load, as the *restore context*:

```python
checkpointer = FilesystemCheckpointer(
    "my-checkpoints",
    restore_context=haiku_checkpoint_restore_context(llm, task_message),
)
```

Anything passed to `from_checkpoint(**context)` is merged over the context given
to the constructor, so you can override individual entries at load time. A
missing operation function raises `ValueError` naming exactly what was absent.

Credentials are deliberately excluded from `llm_to_config`, so a checkpoint never
contains an API key. The key comes from the environment when the model is rebuilt,
or from an explicit `api_key` entry in the restore context.

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
delete the directory and start over deliberately.
