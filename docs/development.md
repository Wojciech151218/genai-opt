# Development

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution guide (branching, commits, PRs, versioning, releases).

## Quick start

```bash
pip install -e ".[dev]"
pre-commit install
```

```bash
pytest
ruff check .
mkdocs build
```

Do not commit directly to `main`. Use typed commit messages:

```bash
git commit -m "feat: add experiment builder"
git commit -m "fix: handle empty population"
git commit -m "docs: add api reference"
```

User-facing release notes go in `CHANGELOG.md`.
