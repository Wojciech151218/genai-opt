# First Experiment

Run the bundled numeric optimizer and inspect its final population. The
example requires a source checkout, not model credentials.

## Basic Usage

From the repository root, activate the environment from
[Installation](installation.md) and start `python` (or `py` on Windows).
Paste this complete example into the interpreter:

```python
from math import isclose

from experiments.simple_experiment import run_simple_experiment
from genai_opt.optimizer_engine import Genome, Population

population: Population[float, float] = run_simple_experiment(
    iterations=3,
    checkpoint_db=None,  # (1)!
)
best: tuple[Genome[float, float], float] = max(
    population.get_genome_fitness(),
    key=lambda item: item[1],
)
best_genome, best_fitness = best

print(population.get_genome_count())
#> 20
print(isclose(best_fitness, 100.0 - abs(best_genome.phenotype - 50.0)))
#> True
print(best_fitness <= 100.0)
#> True
```

1. Disable SQLite checkpoints. Each invocation starts with a new random population.

The exact value of `best_genome.phenotype` varies between runs. Fitness is
`100 - abs(value - target)`; the target is `50.0` by default.

!!! info "Local WebSocket"
    The runner opens a WebSocket on `localhost:8765` while it runs, even
    without the dashboard. It does not call an external model or service.

## Configuration

`run_simple_experiment` evaluates each generation, selects parents with
tournament selection, creates offspring, mutates some of them and replaces the
old population. The returned population has evaluated fitness values.

| Parameter | Type | Default | Effect |
| --- | --- | --- | --- |
| `target` | `float` | `50.0` | Numeric value to approach. |
| `iterations` | `int` | `10` | Number of iterations to run. |
| `mutation_rate` | `float` | `0.2` | Probability of mutating each offspring, not the size of its numeric change. |
| `population_size` | `int` | `20` | Number of candidates per generation. |
| `checkpoint_db` | `str | Path | None` | `.checkpoints/simple_experiment.db` | SQLite path; `None` disables persistence. |
| `launch_ui` | `bool` | `False` | Start the optional dashboard. |

Omit `checkpoint_db=None` to save state at the default path. Reusing that
path loads the saved experiment instead of starting fresh. The other values
are not a guarantee that fitness will improve on every iteration.

## Edge Cases

A zero-sized population can be returned if zero iterations are requested.
Choosing its best genome raises `ValueError` in `max()`:

```python
from experiments.simple_experiment import run_simple_experiment
from genai_opt.optimizer_engine import Population

empty_population: Population[float, float] = run_simple_experiment(
    iterations=0,
    population_size=0,
    checkpoint_db=None,
)
print(empty_population.get_genome_count())
#> 0

try:
    max(empty_population.get_genome_fitness(), key=lambda item: item[1])
except ValueError as error:
    print(type(error).__name__)
    #> ValueError
```

!!! warning "Port already in use"
    A second experiment using `localhost:8765` at the same time cannot
    start its WebSocket server. Stop the other run before retrying.
