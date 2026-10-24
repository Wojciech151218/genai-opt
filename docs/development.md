# Development

This project follows the workflow described in `dev-guide.md` and
`git-versioning-guide.md`.

## Workflow

Use a dedicated branch for each change:

```bash
git checkout main
git pull origin main
git checkout -b feature/my-change
```

Keep commits focused and use typed commit messages:

```bash
git commit -m "feat: add experiment builder"
git commit -m "fix: handle empty population"
git commit -m "docs: add api reference"
```

Do not commit directly to `main`.

## Quality Checks

These are the same checks CI runs, so running them locally first avoids a
round-trip:

```bash
pytest -vv --cov=src/genai_opt --cov-report=term-missing
ruff check .
ruff format --check .
mkdocs build --strict
```

`ruff check` enforces docstrings on every public module, class, function and
method, in Google style. New public API without a docstring fails the build.

CI additionally runs the suite on every supported Python version (3.11, 3.12 and
3.13) and installs the built wheel into a clean environment, since an editable
install hides packaging mistakes.

## Documentation Structure

Reference documentation is generated from docstrings by `mkdocstrings`, so
`docs/api.md` lists what to include rather than restating it. Document behavior in
the docstring, not on the page. Narrative pages — phases, checkpoints, credentials
and cost, API stability — are written by hand.

## Testing Expectations

Important functionality should have tests for:

- normal usage
- invalid input
- edge cases
- previously fixed bugs

When fixing a bug, add or update a test that captures the failing behavior.

## Documentation Expectations

Update documentation when a change affects:

- public API
- installation
- user-facing behavior
- development workflow

User-facing release changes belong in `CHANGELOG.md`. Development decisions and
academic process notes belong in `DEVELOPMENT_LOG.md`.

## AI Usage

Significant AI assistance should be recorded in `AI_USAGE_LOG.md` so the
project remains transparent for academic evaluation.
