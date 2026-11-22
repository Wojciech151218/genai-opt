# Development

See [CONTRIBUTING.md](https://github.com/Wojciech151218/genai-opt/blob/main/CONTRIBUTING.md)
for the project workflow, review requirements, and commit conventions.

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

`ruff check` enforces Google-style docstrings where the documentation lint
rules are enabled. See the per-file exceptions in `pyproject.toml`.

CI additionally runs the suite on every supported Python version (3.11, 3.12 and
3.13) and installs the built wheel into a clean environment, since an editable
install hides packaging mistakes. That packaging smoke lives in
`tests/distribution/test_wheel_smoke.py` and is executed from `/tmp` against the
wheel, not from the checkout.

## Documentation Structure

Reference documentation is generated from docstrings by `mkdocstrings`, so
`docs/api.md` lists what to include rather than restating it. Keep API behavior
in the source docstrings. Use tutorials for runnable examples and guides for
specific tasks. Make clear which decisions belong to the experiment author and
which behavior comes from the library.

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

See the contribution guide for when to update `CHANGELOG.md`.
