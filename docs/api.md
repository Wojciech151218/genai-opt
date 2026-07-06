# API Reference

This page documents the current public API exposed by the package. The project
is still early, so the API should be treated as evolving until a stable release.

## Package Version

```python
import genai_opt

print(genai_opt.__version__)
```

## Genome

`Genome[P, Inv]` is the abstract base for optimization candidates.

Each concrete genome stores a `phenotype` and must implement:

- `invoke()`
- `evaluate()`
- `mutate()`
- `crossover(other)`

Accessing `genome.evaluation` before evaluation raises `ValueError`.

## Population

`Population[P, Inv]` stores genomes and provides helper operations:

- `add_genome(genome)`
- `remove_genome(index)`
- `evaluate_population()`
- `reset_evaluations()`
- `get_genome_and_fitness(index)`
- `get_genome_fitness()`
- `get_genome_count()`
- `merge(other)`

Population evaluation is asynchronous and evaluates all genomes concurrently.

## Engine

`Engine` coordinates the optimization loop.

The loop repeats until the convergence criterion returns `True`:

1. Evaluate the current population.
2. Create offspring through the reproduction policy.
3. Mutate offspring according to the mutation policy.
4. Evaluate offspring.
5. Replace the current population with offspring.
6. Collect metrics.

## ExperimentBuilder

`ExperimentBuilder` wires together:

- initial population strategy
- convergence criterion
- mutation policy
- reproduction policy
- metrics collector

Calling `build()` returns a configured `Engine`.

## Policies and Criteria

Available convergence criterion:

- `iteration_limited_convergence(iteration_limit)`

Available mutation policy:

- `random_mutation(threshold)`

Available parent selection strategies:

- `tournament_selection(population)`
- `roulette_wheel_selection(population)`
- `rank_selection(population)`

Available reproduction helper:

- `generational_reproduction(population_size)`

## Metrics

`TerminalLoggerMetricsCollector` prints iteration number, population size, best
fitness, worst fitness, and mean fitness.

## Example Genome

`FloatGenome` optimizes a single float toward a target value.

Fitness is calculated as:

```python
100.0 - abs(phenotype - target)
```
