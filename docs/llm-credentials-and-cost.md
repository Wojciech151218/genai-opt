# LLM Credentials and Cost

The engine itself never talks to a model. Only LLM-backed genomes do, which means
credentials and spend are properties of the experiment you configure rather than
of the library.

## Supplying credentials

Three options, in the order they are consulted:

1. **Pass a configured model.** Build the chat model yourself and hand it to the
   experiment. This is the clearest option and the only one that works for
   providers other than the default.

```python
from genai_opt.experiments.haiku_experiment import build_haiku_experiment

engine = build_haiku_experiment(my_chat_model, iterations=3).build()
```

2. **Pass a key explicitly.** `run_haiku_experiment(api_key=...)` forwards it to
   the model factory.

3. **Set the environment variable.** `OPENAI_API_KEY` is read from the environment,
   falling back to a `.env` file in the repository root. Existing environment
   variables win over the file, so an exported key is never overridden.

If no key can be found, `create_llm` raises `RuntimeError` immediately rather than
letting the run fail partway through with a provider error.

## Keeping keys out of the repository

- `.env` is listed in `.gitignore`. Keep it that way.
- Checkpoints never contain credentials: only the model name and generation
  settings are stored, and the key is re-supplied when the model is rebuilt.
- Nothing in the library writes to `.env` or logs a key. The terminal controller
  prints model names, never credentials.

## What an iteration costs

Each iteration of an LLM-backed experiment makes roughly:

| Phase | Model calls |
|-------|-------------|
| Evaluate population | one invocation plus one evaluation per genome |
| Reproduce | one crossover per child |
| Mutate | one mutation per selected offspring |
| Evaluate offspring | one invocation plus one evaluation per offspring |

So with `population_size=8` and `mutation_rate=0.35`, a single iteration is on the
order of 40 model calls. The controls that matter are `iterations` (a hard bound on
total spend), `population_size` (per-iteration width) and `mutation_rate`.

The haiku experiment also checks form in code before judging: a poem that is not
5-7-5 scores zero without a model call, so the judging budget goes to poems worth
judging.

## Tracking spend

Every operation carries an
[`LLMMetadata`](api.md#genai_opt.optimizer_engine.operation) record with token
counts and the model name, extracted automatically from the provider's response.
`IterationMetadata` aggregates these into `total_tokens`, `total_cost` and
`total_duration_seconds`, and `tokens_by_kind` breaks usage down by operation.

Cost is the one field nothing fills in automatically, because per-token pricing is
provider- and plan-specific. Token counts are recorded for you; set
`LLMMetadata.cost` yourself if you want the cost totals to be non-zero.

Both the terminal controller and the checkpoint summary report tokens and cost per
phase, so a run's usage is visible while it happens and after it finishes.

## Running without spending anything

Pass a stub chat model to `build_haiku_experiment` instead of calling
`run_haiku_experiment`. Because every genome operation is injected as a function,
no real provider is required — this is exactly how the test suite exercises the
LLM-backed paths. For engine behavior unrelated to prompts, use
[`FloatGenome`](api.md#genai_opt.experiments.float_genome.FloatGenome), which needs
no network access at all.
