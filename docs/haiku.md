# Optimize a Prompt

The bundled haiku experiment treats **system prompts**, not poems, as
candidates. It uses the same engine as the numeric demo. The task, scoring
rules, and prompts that drive mutation and crossover are specific to the
example, not requirements of the library.

## Basic Usage

From a [source checkout](installation.md#install-from-source), set
`OPENAI_API_KEY` in the environment or in the repo's local `.env` file. Read
[LLM Credentials and Cost](llm-credentials-and-cost.md) before running.

!!! warning "This example calls a real model"
    The default model is `gpt-4o-mini`. Even a one-iteration run may make more
    than one request and incur charges. Do not paste a real key into the script
    or commit your `.env` file.

```python
from experiments.haiku_experiment import print_best_result, run_haiku_experiment


def main() -> None:
    population = run_haiku_experiment(iterations=1, population_size=2)
    print(population.get_genome_count())
    #> 2
    print_best_result(population)


if __name__ == "__main__":
    main()
```

The script prints the best evolved system prompt, its fitness, and a sample
haiku. The poem and score depend on the model's responses. The dashboard is
off by default; the runner still uses the local WebSocket port `8765`.

## How Candidates Are Scored

| Operation | What the example does |
| --- | --- |
| Invoke | Ask the chat model to write a poem using the candidate's system prompt. All candidates in a run get the same task message. |
| Evaluate | First check English syllable counts using a local heuristic. If the structure is not 5-7-5, return `0.0`. Otherwise ask a model to identify cultural references and rate their significance. Fitness is the number of references multiplied by the significance score. |
| Mutate | Ask the model to revise one system prompt. |
| Crossover | Ask the model to combine two system prompts. |

## Adapt the Example

For a different task, provide your own starting prompts, task message,
structured output schema, and scoring rule. The
[system prompt adapter](api.md#system-prompt-adapter) lets you supply the
operations as functions instead of writing a genome subclass. For a
credential-free test, use `build_haiku_experiment(llm)` with a stub model instead
of initializing a provider through the runner.

The quick example stores checkpoints in `.checkpoints/haiku_experiment.db`.
The runner generates a fresh `experiment_id` when omitted; resuming requires
the same database path and an explicit, matching ID. If the task itself must
be identical after resuming, use a builder with a fixed `shared_task`: the
runner picks a task anew on each call.
