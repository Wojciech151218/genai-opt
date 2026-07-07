# Getting Started

## Requirements

The package declares support for Python `>=3.13` in `pyproject.toml`.

For local development, install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

## Verify Installation

Run the test suite:

```bash
pytest
```

Run the code style check:

```bash
ruff check .
```

## Run the Simple Experiment

The project includes a small experiment that evolves float values toward a
target value.

```python
import asyncio

from genai_opt.experiments.simple_experiment import run_simple_experiment


population = asyncio.run(
    run_simple_experiment(
        target=50.0,
        iterations=10,
        mutation_rate=0.2,
        population_size=20,
    )
)

best_genome, best_fitness = max(
    population.get_genome_fitness(),
    key=lambda item: item[1],
)

print(best_genome.phenotype, best_fitness)
```

## Build Documentation

Serve documentation locally:

```bash
mkdocs serve
```

Build the static site:

```bash
mkdocs build
```
