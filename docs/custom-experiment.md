# Build Your Own Experiment

Define what a candidate is, how to run and score it, and how to make new
candidates. Use `ExperimentBuilder` to combine those operations with the engine's
selection, mutation, reproduction, and stopping policies.

## Basic Usage

This example chooses a batch size using a toy model: useful work grows up to
eight items per batch, but larger batches keep incurring a penalty. It is not a
benchmark. The example uses only the installed library, without a model,
dashboard, or database.

```python
from random import choice
from typing import Self

from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Genome,
    Operation,
    Population,
    ReproductionPolicy,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
)


class BatchSize(Genome[int, int]):
    async def invoke(self) -> Operation[int]:
        return Operation(min(self.phenotype, 8))  # (1)!

    async def evaluate(self) -> Operation[float]:
        return Operation(float(3 * self.invocation - self.phenotype))  # (2)!

    async def mutate(self) -> Operation[Self]:
        size: int = self.phenotype + choice((-1, 1))
        return Operation(type(self)(max(1, min(16, size))))

    async def crossover(self, other: Genome[int, int]) -> Operation[Self]:
        return Operation(type(self)((self.phenotype + other.phenotype) // 2))


def initial_population() -> Population[int, int]:
    return Population([BatchSize(size) for size in (2, 4, 8, 16)])


def main() -> None:
    builder: ExperimentBuilder[int, int] = ExperimentBuilder(
        inital_population_strategy=initial_population,  # (3)!
        convergence_criterion=iteration_limited_convergence(3),
        mutation_policy=random_mutation(0.25),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(4), tournament_selection
        ),
    )
    population: Population[int, int] = builder.build().run()
    candidate, fitness = max(population.get_genome_fitness(), key=lambda item: item[1])

    print(population.get_genome_count())
    #> 4
    print(fitness == 3 * candidate.invocation - candidate.phenotype)
    #> True


if __name__ == "__main__":
    main()
```

1. The first `int` in `Genome[int, int]` is the batch size; the second is the
   output produced when the candidate runs.
2. Return a score to maximize. The engine runs `invoke()` before `evaluate()`,
   so `self.invocation` contains the result to score.
3. The constructor currently spells this keyword `inital_population_strategy`.
   Pass the callable itself so the builder can create a new population at build time.

## What To Customize

| Decision | Where to implement it |
| --- | --- |
| What one candidate represents and what it produces | The phenotype and `Genome.invoke()`. |
| What makes a result good | `Genome.evaluate()`. Return a numeric fitness; higher is better. |
| How to vary or combine candidates | `Genome.mutate()` and `Genome.crossover()`. Return new genomes; do not change the parents. |
| How to initialize, select, reproduce, and stop | The initial population strategy and the policies passed to `ExperimentBuilder`. |
| What to store or expose while running | An optional [checkpointer](checkpoints.md) or [controller](websocket-controller.md). |

!!! info "Mutation probability and mutation behavior are separate"
    `random_mutation(0.25)` decides which offspring to mutate. In this example,
    `BatchSize.mutate()` decides how: shift the size by one, then keep it between
    `1` and `16`.

The returned population is the final generation, not an archive of every
candidate seen. If you need to compare generations, inspect
[phase metadata](phases.md) or save [checkpoint history](sqlite-checkpointer.md).

## Edge Cases

`Genome.evaluation` raises `ValueError` before the engine evaluates that
genome. For example, in the same script, `BatchSize(8).evaluation` fails with
`ValueError: Genome has not been evaluated`. Do not rank a fresh population
until it has been evaluated. Likewise, an empty population has no maximum.

If you enable checkpointing, keep custom genome classes in importable modules
and implement the [restore hooks](checkpoints.md#restore-context) they need.
For candidates that are system prompts, see [Optimize a Prompt](haiku.md) for a
ready-made adapter instead of writing a new genome class.
