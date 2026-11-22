# genai-opt

<div class="docs-badges" aria-label="Project information">
  <span class="docs-badge"><span>version</span><strong>0.3.1</strong></span>
  <span class="docs-badge"><span>python</span><strong>3.11+</strong></span>
  <span class="docs-badge"><span>license</span><strong>MIT</strong></span>
</div>

`genai-opt` is a Python library for building and running evolutionary
optimization experiments. You define what a candidate represents, how to run and
score it, and how to vary it. The engine runs those operations across generations
using your chosen policies.

## Quick Example

This bundled demo evolves numbers toward `50.0`. It illustrates the engine; it
is not a built-in mode of the library. Run it from a repository checkout with
development dependencies installed:

```python
from math import isclose

from experiments.simple_experiment import run_simple_experiment
from genai_opt.optimizer_engine import Genome, Population

population: Population[float, float] = run_simple_experiment(
    iterations=3, checkpoint_db=None
)
best: tuple[Genome[float, float], float] = max(
    population.get_genome_fitness(), key=lambda item: item[1]
)
best_genome, fitness = best
print(isclose(fitness, 100.0 - abs(best_genome.phenotype - 50.0)))
#> True
```

Higher fitness is better. The numeric result varies between runs; the
[First Experiment](getting-started.md) explains the configuration and output.

!!! note "Examples live in the repository"
    The installed wheel includes the library, but `experiments/` is available
    from a source checkout, not the installed wheel.

## How It Works

| You define | The library provides |
| --- | --- |
| The candidate representation, what running it produces, and what score counts as better. | `Genome`, `Operation`, and `Population` to represent and evaluate candidates. |
| The starting population, selection, mutation probability, reproduction, and when to stop. | `ExperimentBuilder`, reusable policies, and an `Engine` that executes the [iteration phases](phases.md). |
| Whether to persist or observe the run. | Optional [checkpointers](checkpoints.md), [controllers](api.md#experiment-control), and a [local dashboard](web-dashboard.md). |

## Next Steps

| Page | What you will learn |
| --- | --- |
| [Installation](installation.md) | Install the library or prepare a source checkout. |
| [First Experiment](getting-started.md) | Run the bundled numeric demo without model credentials. |
| [Build Your Own Experiment](custom-experiment.md) | Define a candidate and assemble a run using only the installed library. |
| [Optimize a Prompt](haiku.md) | See how the same engine can evolve prompts with a chat model. |
| [API Reference](api.md) | Look up library classes, policies, and extension points. |
