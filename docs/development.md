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

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Build docs:

```bash
mkdocs build
```

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
