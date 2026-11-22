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

`engine.run()` is the ordinary entry point. It owns the event loop, loops
until the convergence criterion is satisfied, and returns the final population.

Because it calls `asyncio.run()` internally, it cannot be used from inside a
running event loop. In a notebook, a web handler, or any other async context,
await `step()` yourself instead. In this example from a source checkout, the
caller drives exactly one iteration and manages the controller lifecycle:

```python
import asyncio

from experiments.simple_experiment import build_simple_experiment
from genai_opt.optimizer_engine import Engine


async def run_one_iteration() -> None:
    engine: Engine[float, float] = build_simple_experiment(websocket_port=0).build()
    controller = engine.experiment_controller
    await controller.setup()
    try:
        while engine.iteration < 1:
            await engine.step()
        print(engine.iteration)
        #> 1
    finally:
        await controller.teardown()


if __name__ == "__main__":
    asyncio.run(run_one_iteration())
```

Driving `step()` directly is also how you interleave the engine with your own
work: it returns the metadata for the phase that just ran, so you can inspect
fitness, token usage and cost after each one. Unlike `run()`, a direct call to
`step()` does not apply the convergence criterion. Your loop decides when to
stop. Port `0` lets the operating system choose a free local port.

## Convergence is only checked between iterations

The convergence criterion is consulted at the top of an iteration, when the next
phase is `EVALUATE_POPULATION`. A criterion that becomes true midway through an
iteration therefore takes effect once the remaining phases have finished, so a
generation is never left half-built.

To suspend a run, use an [experiment controller](api.md#experiment-control).
The engine checks for a pause before the next phase; a controller can also wait
at its callbacks during a phase.
