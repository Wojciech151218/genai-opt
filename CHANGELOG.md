# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-28

First release published to PyPI, and the point from which the public API is
covered by semantic versioning. See [API stability](docs/api-stability.md) for
what that commits us to.

The 0.1.0 entry below described only a project scaffold and was never updated,
so this entry covers everything the library actually does.

### Added

- **Optimizer engine.** `Engine` runs a genetic algorithm over a `Population` of
  `Genome` objects. Each iteration is split into five explicit phases — evaluate
  population, reproduce, mutate, evaluate offspring, replace — which can be driven
  one at a time with `step()` or continuously with `run()`.
- **Resumable runs.** `FilesystemCheckpointer` records the engine state after
  every phase, so a run interrupted mid-iteration resumes from that phase rather
  than restarting it. This matters when a phase costs real money in LLM calls.
  `NullCheckpointer` opts out.
- **Live observation and pausing.** `ExperimentController` receives each phase,
  and each individual operation as it completes, so a slow LLM-backed generation
  is visible while it is still running. `TerminalController` implements this as a
  colored log with cooperative pause and resume on the `p` key.
- **Composable strategies.** Convergence, initial population, parent selection,
  reproduction and mutation are all injected functions, with defaults provided
  (`iteration_limited_convergence`, `cycle_seeds_initial_population_strategy`,
  `tournament_selection`, `generational_reproduction`, `random_mutation`).
  `ExperimentBuilder` assembles them into an engine.
- **Cost and token accounting.** Every LLM call is recorded as an `Operation`
  carrying token counts, duration and model metadata, aggregated per phase by
  `IterationMetadata`, so the price of a run is measurable rather than estimated.
- **Prompt optimization adapter.** `SimpleSystemPromptGenome` optimizes an LLM
  system prompt, with LLM-driven and text-level mutation, crossover and
  evaluation functions, plus `mixed_mutate_function`, which falls back to a
  simpler strategy when a mutation fails.
- **Example experiments.** `FloatGenome` for a dependency-free numeric run, and a
  haiku experiment that optimizes a prompt against an LLM judge.
- **`TerminalLoggerMetricsCollector`**, a standalone helper for summarizing
  collected metadata. It is documented as optional and is not called by the
  engine; `ExperimentController` is the engine-invoked reporting hook.
- **Typed public API.** The package ships `py.typed`, so the generic engine
  annotations reach type checkers in consuming projects.

### Changed

- Python 3.11 is now the minimum supported version, down from 3.13. Nothing in
  the library needed 3.13; the only blockers were PEP 695 type-alias and generic
  syntax, now written as `TypeAlias` and `TypeVar`. The test suite runs on 3.11,
  3.12 and 3.13.
- Documentation is generated from docstrings, and undocumented public API now
  fails the lint step, so the reference cannot drift from the code.

### Fixed

- `import genai_opt.experiments.simple_experiment` raised `ModuleNotFoundError`
  on Windows, because `TerminalController` imported `termios` and `tty` at module
  scope. Key reading now goes through a `KeyReader` chosen at runtime, with POSIX,
  Windows and no-op backends that import their platform modules lazily. The
  no-op backend also covers non-interactive stdin, so runs in CI and notebooks no
  longer depend on terminal behavior.
- `TerminalController` leaked its keypress listener task and left the terminal in
  cbreak mode, since `setup()` had no counterpart. `ExperimentController.teardown()`
  now exists and the engine calls it in a `finally`, so the terminal is restored
  even when a run fails.
- The terminal was reconfigured twice per 50 ms poll; cbreak mode is now entered
  once per run.
- A corrupt or unrecognized checkpoint raised an unclear error or, worse, could
  be misread. Checkpoint loading now rejects malformed payloads, unknown genome
  types and unrecognized phases with an explicit message, so a broken checkpoint
  fails loudly rather than silently discarding a run's progress.

### Removed

- `EngineConfig`, a mutable global singleton that nothing imported and whose only
  field was never read. Removed rather than frozen into the 1.0 API.

## [0.1.0] - 2026-07-01

### Added

- Initial project scaffold
