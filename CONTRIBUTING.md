# Contributing

How to develop and release changes in this project.

For CI details, see [cicd.md](cicd.md) if present.

---

## Setup

```bash
git clone https://github.com/Wojciech151218/genai-opt.git
cd genai-opt

python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pre-commit install
```

Local checks:

```bash
pytest --cov=src/genai_opt --cov-report=term-missing
ruff check .
ruff format --check .
mkdocs build
```

This project uses **Ruff**, **pre-commit**, and **pytest**. If a commit is blocked by pre-commit, review the auto-fixes, `git add` again, and retry.

---

## Principles

1. **`main` is always releasable** — working, tested code only.
2. **All changes go through branches and PRs** — never commit directly to `main`.
3. **One logical change per commit** — easy to review and revert.
4. **Versions are explicit** — releases are tagged and recorded in `CHANGELOG.md`.

---

## Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable integration branch; release-ready only |

Rules for `main`:

- Do not push commits directly.
- Every change enters via a pull request.
- CI must pass before merge.
- At least one team member must review before merge.

### Naming

Use lowercase, hyphen-separated names with a type prefix:

| Prefix | Use for | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/float-genome` |
| `fix/` | Bug fixes | `fix/import-error` |
| `docs/` | Documentation only | `docs/api-examples` |
| `test/` | Test-only changes | `test/optimizer-edge-cases` |
| `chore/` | Tooling, deps, housekeeping | `chore/ruff-config` |
| `release/` | Version bump and release prep | `release/v0.2.0` |

```bash
git checkout main
git pull origin main
git checkout -b feature/parser
```

### Lifecycle

1. Branch from `main`.
2. Make small, focused commits.
3. Push and open a PR.
4. Address review feedback.
5. Merge after CI passes and review is approved.
6. Delete the branch after merge.

Keep branches short-lived. If a branch lives more than a few days, merge or rebase `main` into it regularly:

```bash
git checkout feature/parser
git fetch origin
git merge origin/main
```

---

## Commits

Each commit should be a single coherent change.

### Message format

```
<type>: <short summary>

[optional body — explain why, not just what]

[optional footer — issue references]
```

| Type | When to use |
|------|-------------|
| `feat` | New feature or behavior |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that is not a fix or feature |
| `chore` | Build, tooling, dependencies |
| `ci` | CI/CD configuration |

Summary rules:

- Imperative mood: **"Add parser"**, not "Added parser".
- Under ~72 characters; no trailing period.
- Specific enough that `git log --oneline` is useful.

**Good:**

```
feat: add float genome representation

fix: handle empty population in optimizer engine

docs: update contributing guide

test: cover invalid genome bounds in float_genome

chore: bump ruff to 0.8.x
```

**Bad:** `Update`, `fixed stuff`, `Final version`, `WIP`

### When to commit

- A small piece of work is complete and runs.
- Tests pass for the changed area.
- You are about to switch tasks or stop for the day.

Do not commit secrets (`.env`, credentials), virtualenvs, or unrelated mixed changes.

```bash
git status
git diff
git add -p
git commit -m "feat: add experiment builder"
```

---

## Pull requests

### Title

Same style as commit summaries:

```
feat: add simple experiment runner
fix: correct import path in optimizer engine
```

### Description

Include what changed, why, and how to test:

```markdown
## Summary
Add a minimal experiment runner for the optimizer engine.

## Motivation
We need an end-to-end path to evaluate genomes before adding GenAI helpers.

## Test plan
- [ ] `pytest tests/test_simple_experiment.py`
- [ ] Run example from README
```

### Checklist

- [ ] Branch is up to date with `main`
- [ ] CI passes
- [ ] Tests added or updated for behavior changes
- [ ] Documentation updated if user-facing behavior changed
- [ ] `CHANGELOG.md` updated if this will be part of the next release
- [ ] No secrets or local-only files included
- [ ] Commit messages follow this guide

### Merge

- Require at least one approving review and green CI.
- Prefer squash merge for noisy feature branches, or keep a clean rebase history — pick one per PR.
- Delete the source branch after merge.

### Review focus

Correctness, maintainability, fit with project design, test coverage, and obvious security issues (secrets, unsafe defaults).

---

## Testing

Important functionality should have tests for normal usage, invalid input, edge cases, and previously fixed bugs.

When fixing a bug: add a failing test, fix the code, confirm the test passes.

```bash
pytest --cov=src/genai_opt --cov-report=term-missing
```

---

## Documentation

| File | Audience | Contents |
|------|----------|----------|
| `README.md` | Users | Description, install, usage |
| `CHANGELOG.md` | Users | Released changes (Keep a Changelog) |
| Docs under `docs/` | Users / developers | API and guides |

Update docs when a change affects public API, installation, user-facing behavior, or this workflow.

---

## Versioning and releases

[Semantic Versioning 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

| Change | Bump | Example |
|--------|------|---------|
| Breaking API or behavior | MAJOR | `0.1.0` → `1.0.0` |
| Backward-compatible feature | MINOR | `0.1.0` → `0.2.0` |
| Backward-compatible bug fix | PATCH | `0.2.0` → `0.2.1` |

While at `0.x.y`, bump MINOR for features and PATCH for fixes. `1.0.0` means a stable public API.

### Where the version lives

Canonical version in `src/genai_opt/__init__.py`:

```python
__version__ = "0.1.0"
```

`pyproject.toml` reads it via setuptools dynamic versioning. Release tags `vX.Y.Z` must match this string.

Bump the version only on a release PR — not on every feature PR.

### Changelog

Record user-facing changes in [CHANGELOG.md](CHANGELOG.md):

```markdown
## [0.2.0] - 2026-07-15

### Added
- Simple experiment runner

### Fixed
- Import error in optimizer engine
```

Groups: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

### Release checklist

- [ ] Planned changes merged to `main`
- [ ] Full test suite passes locally and in CI
- [ ] Version bumped in `src/genai_opt/__init__.py`
- [ ] `CHANGELOG.md` updated with date and entries
- [ ] README / docs reflect current usage
- [ ] Version-bump PR reviewed and merged (`release/vX.Y.Z` if useful)

### Tagging

```bash
git checkout main
git pull origin main
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

Flow: feature branches → PRs → `main` → version bump + CHANGELOG → tag `vX.Y.Z` → GitHub Release / PyPI as configured.

---

## Common scenarios

**New feature**

```bash
git checkout main && git pull origin main
git checkout -b feature/my-feature
# ... work, commit ...
git push -u origin feature/my-feature
# Open PR
```

**Bug fix**

```bash
git checkout main && git pull origin main
git checkout -b fix/issue-description
# ... fix, add test, commit ...
git push -u origin fix/issue-description
```

**Release 0.2.0**

```bash
git checkout main && git pull origin main
git checkout -b release/v0.2.0
# bump __version__, finalize CHANGELOG
git commit -m "chore: release v0.2.0"
git push -u origin release/v0.2.0
# Open PR, merge, then tag on main
```

---

## What not to do

| Do not | Why |
|--------|-----|
| Commit directly to `main` | Bypasses review and CI |
| Force-push to `main` | Rewrites shared history |
| Merge with failing CI | Breaks the stable branch |
| Use vague commit messages | Harder to review and debug |
| Bump version on every PR | Noisy releases |
| Commit secrets or `.env` | Security risk |
| Leave stale branches forever | Clutters the repo |

---

## Quick reference

```
feature/<desc> | fix/<desc> | docs/<desc> | release/vX.Y.Z

<type>: <imperative summary>

MAJOR.MINOR.PATCH     (e.g. 0.2.1)
tag: vMAJOR.MINOR.PATCH
```

```
branch from main
  → focused commits
  → PR + CI + review
  → merge
  → on release: bump version + CHANGELOG + tag vX.Y.Z
```
