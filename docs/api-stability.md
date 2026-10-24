# API Stability

This project follows [Semantic Versioning](https://semver.org/). From 1.0.0 the
public API is stable: a breaking change requires a major version bump.

## What is public

Anything exported from a package's `__all__` and reachable without touching an
underscore-prefixed name:

- `genai_opt.__version__`
- everything in `genai_opt.optimizer_engine`
- everything in `genai_opt.adapters` and its adapter packages
- the example experiments in `genai_opt.experiments`

Type hints ship with the package: a `py.typed` marker is included, so type
checkers use the annotations directly.

## What is not public

- Any name beginning with an underscore, including `Engine._state`,
  `Genome._invoke` and the `_from_json` hook. Subclasses do override
  `_from_json` and `_restore_runtime_state`; those two are documented for that
  reason, but they may change in a minor release.
- `genai_opt.optimizer_engine.utils`, which holds internal typing aliases.
- The exact wording and layout of terminal output.

## Checkpoint compatibility

Checkpoints are a serialization format, not an API, and they are versioned only by
what they contain. Within a major version an existing checkpoint stays readable
unless *your own* genome classes or invocation schemas move or change
incompatibly — see [Checkpoints and Resuming](checkpoints.md) for the specific
cases and the errors they raise.

## Supported Python versions

3.11 and newer. Dropping a Python version is treated as a breaking change and
requires a major version bump.

Every supported version is tested in CI on each pull request, and the release
pipeline reruns those checks before publishing.

## Platform support

The library is platform-agnostic and imports cleanly on Linux, macOS and Windows.
Interactive pause and resume in `TerminalController` requires a terminal: on POSIX
hosts it uses `termios`, on Windows `msvcrt`, and where stdin is not a TTY — CI
logs, piped input, notebooks — it silently falls back to log-only output rather
than failing.
