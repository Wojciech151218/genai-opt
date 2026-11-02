# genai-opt

<div class="docs-badges" aria-label="Project information">
  <span class="docs-badge"><span>version</span><strong>0.3.1</strong></span>
  <span class="docs-badge"><span>python</span><strong>3.11+</strong></span>
  <span class="docs-badge"><span>license</span><strong>MIT</strong></span>
</div>

`genai-opt` runs evolutionary optimization experiments, including experiments
over LLM prompts. Candidates define how to run and score a solution; the engine
handles selection, mutation and reproduction.

## Quick Example

From a repository checkout with development dependencies installed:

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

A `Genome` represents one candidate. A `Population` groups candidates, and the
`Engine` evaluates them, selects parents, creates offspring and runs the next
iteration. Policies control selection, mutation and the stopping condition.

Checkpoints are optional. Set `checkpoint_db=None` as above to start fresh on
every run; keep the default SQLite path to resume saved progress.

## Next Steps

| Page | What you will learn |
| --- | --- |
| [Installation](installation.md) | Install the library or prepare a source checkout. |
| [First Experiment](getting-started.md) | Run and understand a credential-free experiment. |
