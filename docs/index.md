# genai-opt

`genai-opt` is a Python library designed for building and running optimization experiments. The current codebase focuses on a generic evolutionary optimizer
with asynchronous genome evaluation, configurable reproduction, mutation, convergence criteria, and metrics collection.

## Current Scope

- Generic `Genome` abstraction for phenotype-based optimization.
- `Population` container with asynchronous evaluation support.
- `Engine` loop for evaluate, reproduce, mutate, evaluate offspring, replace,
  and collect metrics.
- Reproduction policies with tournament, roulette wheel, and rank selection.
- Mutation policy based on a probability threshold.
- Iteration-limited convergence criterion.
- A simple `FloatGenome` experiment that optimizes a float toward a target.

## Project Status

The project is in an early `0.1.0` stage. Public APIs may still evolve, but
changes should follow the workflow described in the development guides:
branches, focused commits, tests, review, and documentation updates.

## Quick Commands

```bash
pip install -e ".[dev]"
pytest
ruff check .
mkdocs serve
```
