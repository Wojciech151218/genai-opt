# genai-opt

`genai-opt` is a Python library for building and running evolutionary
optimization experiments, including ones whose candidates are LLM prompts.

The engine is generic: you describe a candidate as a `Genome` with four
operations — invoke, evaluate, mutate and crossover — and the engine handles
selection, iteration, concurrency and persistence.

## What it provides

- A generic `Genome` abstraction, and a `Population` that invokes and evaluates
  its members concurrently, streaming results as they finish.
- An `Engine` loop split into [five resumable phases](phases.md), so an
  interrupted run continues rather than repeating paid work.
- [Checkpointing](checkpoints.md) to disk after every phase, with a restore
  context for collaborators that cannot be serialized.
- Live [experiment control](api.md#experiment-control): every phase and operation
  is reported as it happens, and a run can be paused. Works on POSIX and Windows.
- Reproduction with tournament, roulette wheel and rank selection; probability
  based mutation; iteration-limited convergence.
- Token, duration and cost accounting on every operation, aggregated per phase.
- A ready-made adapter for evolving the system prompt of a chat model.
- Two example experiments: a credential-free float optimizer, and a haiku
  prompt optimizer that calls a real LLM.

## Quick start

```bash
pip install -e ".[dev]"
pytest
```

```python
from genai_opt.experiments.simple_experiment import run_simple_experiment

population = run_simple_experiment(iterations=10, checkpoint_dir=None)
best_genome, best_fitness = max(population.get_genome_fitness(), key=lambda item: item[1])
print(best_genome.phenotype, best_fitness)
```

See [Getting Started](getting-started.md) for a fuller walkthrough, including
building an experiment from parts rather than calling a canned runner.

## Requirements and status

Python 3.11 or newer, on Linux, macOS or Windows.

From 1.0.0 the public API is stable under [Semantic Versioning](api-stability.md).
