# Getting Started

## Requirements

Python 3.11 or newer, on Linux, macOS or Windows.

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Verify the installation

```bash
pytest
ruff check .
ruff format --check .
```

## Run the bundled experiment

The simplest experiment evolves float values toward a target. It needs no
credentials and no network access.

```python
from genai_opt.experiments.simple_experiment import run_simple_experiment

population = run_simple_experiment(
    target=50.0,
    iterations=10,
    mutation_rate=0.2,
    population_size=20,
    checkpoint_dir=None,
)

best_genome, best_fitness = max(
    population.get_genome_fitness(),
    key=lambda item: item[1],
)

print(best_genome.phenotype, best_fitness)
```

Leave `checkpoint_dir` at its default and the run saves its progress, so calling
the function again continues where it stopped instead of starting over. See
[Checkpoints and Resuming](checkpoints.md).

## Build an experiment from parts

The canned runners are conveniences. Underneath, an experiment is four decisions
handed to `ExperimentBuilder`: where the first generation comes from, when to
stop, which offspring to mutate, and how to reproduce.

```python
from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Population,
    ReproductionPolicy,
    TerminalController,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
)

engine = ExperimentBuilder(
    inital_population_strategy=lambda: Population([FloatGenome(0.0) for _ in range(20)]),
    convergence_criterion=iteration_limited_convergence(10),
    mutation_policy=random_mutation(0.2),
    reproduction_policy=ReproductionPolicy(
        generational_reproduction(20),
        tournament_selection,
    ),
    experiment_controller=TerminalController(),
).build()

population = engine.run()
```

The `TerminalController` prints each phase and operation as it happens, and lets
you pause the run by pressing `p`. Add a `checkpointer` to make the run resumable.

For finer control than `run()` — driving the loop from an existing event loop, or
stopping on your own terms — see [Iteration Phases](phases.md).

## Write your own genome

Subclass `Genome` and implement the four operations. Fitness is whatever
`evaluate` returns, and higher is better.

```python
from genai_opt.optimizer_engine import Genome, Operation


class MyGenome(Genome):
    async def invoke(self) -> Operation[str]:
        return Operation(str(self.phenotype))

    async def evaluate(self) -> Operation[float]:
        return Operation(float(len(self.invocation)))

    async def mutate(self) -> Operation["MyGenome"]:
        return Operation(MyGenome(self.phenotype + 1))

    async def crossover(self, other: Genome) -> Operation["MyGenome"]:
        return Operation(MyGenome((self.phenotype + other.phenotype) // 2))
```

To checkpoint it, also override `to_json` and `_from_json`; see
[`Genome`](api.md#genai_opt.optimizer_engine.genome.Genome).

## Optimize an LLM prompt

For prompt optimization you do not need a genome subclass at all — the
[system prompt adapter](api.md#system-prompt-adapter) composes one from functions.
Read [LLM Credentials and Cost](llm-credentials-and-cost.md) first: those runs call
real models and spend real money.

## Build the documentation

```bash
mkdocs serve   # live preview
mkdocs build   # static site
```
