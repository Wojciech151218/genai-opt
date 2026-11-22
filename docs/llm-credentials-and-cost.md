# LLM Credentials and Cost

The engine does not call models itself. Credentials and spend depend on the
genome operations you choose for your experiment.

## Supplying Credentials

The [haiku runner](haiku.md) uses these options in order:

1. **Configured model.** Pass `llm` to the runner to bypass the default OpenAI
   setup. You can also pass the model to `build_haiku_experiment()` to configure
   the engine without running it yet.
2. **Explicit key.** Pass `api_key` to the runner when letting it create the
   default chat model.
3. **Environment.** Set `OPENAI_API_KEY` in the environment or in the local
   `.env` file at the checkout root. An existing environment variable takes
   precedence over the file.

If the default model needs a key and none is found, `load_openai_api_key()`
raises `RuntimeError` before the engine starts.

!!! warning "Keep keys out of experiment data"
    Do not commit `.env` or put a key directly into sample code. The built-in
    prompt adapter omits the API key from serialized model settings, but
    checkpoints can still contain prompts, responses, and custom genome fields.

## What Uses Model Calls

For a prompt experiment such as haiku, the usual pattern is:

| Phase | Requests |
| --- | --- |
| Evaluate population | Generate an output and optionally judge it for each candidate. |
| Reproduce | Combine two prompts for each child. |
| Mutate | Revise the prompt for each selected child. |
| Evaluate offspring | Generate and optionally judge the children's outputs. |
| Replace | No model calls. |

The haiku example assigns zero fitness without calling the judge if the poem
fails its local 5-7-5 check. Lowering `iterations`, `population_size`, or
`mutation_rate` reduces planned work, but an iteration limit is not a spending
cap. Billing also depends on token counts, provider rates, and retries.

## Tracking Usage

An operation with model usage can carry an `LLMMetadata` record.
`IterationMetadata` aggregates reported tokens, cost, and duration per
phase. If you want cost totals, supply `LLMMetadata.cost` yourself; the
library does not apply provider prices. Zero recorded cost does not imply
that a request was free.

## Running Without a Provider

Pass a stub chat model to `build_haiku_experiment()` to test prompt operations
without making requests. To try the engine without a model at all, use
[First Experiment](getting-started.md) or
[Build Your Own Experiment](custom-experiment.md).
