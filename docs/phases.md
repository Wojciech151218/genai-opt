# Iteration Phases

An iteration is not one indivisible step. The engine splits it into five phases
and executes exactly one per call to `Engine.step()`.

## The five phases

| Order | Phase | What happens |
|-------|-------|--------------|
| 1 | `EVALUATE_POPULATION` | Every genome in the current generation is invoked and scored. |
| 2 | `REPRODUCE` | Parents are selected and crossed over into an offspring generation. |
| 3 | `MUTATE` | The mutation policy is applied to those offspring. |
| 4 | `EVALUATE_OFFSPRING` | The offspring are invoked and scored. |
| 5 | `REPLACE` | Offspring become the current generation and the iteration counter advances. |

The phase stored in the engine's state is always the *next* one to execute, which
is what makes a checkpoint safe to resume without repeating completed work.

## `run()` versus `step()`

`run()` is the ordinary entry point. It owns the event loop, loops until the
convergence criterion is satisfied, and returns the final population:

```python
population = engine.run()
```

Because it calls `asyncio.run()` internally, it cannot be used from inside a
running event loop. In a notebook, a web handler, or any other async context,
drive `step()` yourself instead:

```python
while engine._state.phase is not IterationPhase.EVALUATE_POPULATION or not engine.convergence_criterion(
    engine.population, engine.iteration
):
    metadata = await engine.step()
```

Driving `step()` directly is also how you interleave the engine with your own
work: it returns the metadata for the phase that just ran, so you can inspect
fitness, token usage and cost after each one and stop early on your own terms.

## Reusing stored evaluations

By default, the engine invokes and evaluates every genome during
`EVALUATE_POPULATION`, even if that genome already has a fitness from the
previous `EVALUATE_OFFSPRING` phase. Set `reuse_evaluations=True` on
`ExperimentBuilder` or `Engine` to skip genomes that already have both a stored
invocation result and fitness:

```python
from experiments.simple_experiment import build_simple_experiment

engine = build_simple_experiment(reuse_evaluations=True).build()
```

This can save model calls when evaluation is expensive. It also means the engine
keeps the existing fitness instead of sampling a fresh invocation and score.
That tradeoff matters when model outputs or an LLM judge are stochastic. The
option defaults to `False`, preserving the existing behavior. Newly created
offspring have no stored result and are always evaluated. Reuse the score only
when the task and evaluation setup have not changed since that score was produced.

## Convergence is only checked between iterations

The convergence criterion is consulted at the top of an iteration, when the next
phase is `EVALUATE_POPULATION`. A criterion that becomes true midway through an
iteration therefore takes effect once the remaining phases have finished, so a
generation is never left half-built.

To stop sooner than that, pause the run through an
[experiment controller](api.md#experiment-control), which takes effect before the
next phase begins.
