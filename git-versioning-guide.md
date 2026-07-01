# Git and Versioning Guide

## Purpose

This document defines how we use Git and version numbers in this project.

It covers:

- Branching rules
- Commit message conventions
- Pull request workflow
- Semantic versioning
- Release tagging

For the broader development process, see [dev-guide.md](dev-guide.md).  
For CI checks and branch protection, see [cicd.md](cicd.md).

---

# 1. Core Principles

1. **`main` is always releasable** — it contains working, tested code.
2. **All changes go through branches** — never commit directly to `main`.
3. **One logical change per commit** — commits should be easy to review and revert.
4. **History should tell a story** — messages explain *what* changed and *why*.
5. **Versions are explicit** — releases are tagged and documented in `CHANGELOG.md`.

---

# 2. Branching

## 2.1 Protected Branch

| Branch | Purpose |
|--------|---------|
| `main` | Stable integration branch; release-ready code only |

Rules for `main`:

- Do not push commits directly to `main`.
- Every change enters `main` through a pull request (PR).
- CI must pass before merging (see [cicd.md](cicd.md)).
- At least one team member must review the PR before merge.

## 2.2 Working Branches

Create a branch for every task: feature, bug fix, documentation update, or release prep.

Start from an up-to-date `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/parser
```

## 2.3 Branch Naming

Use lowercase, hyphen-separated names with a type prefix:

| Prefix | Use for | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/float-genome` |
| `fix/` | Bug fixes | `fix/import-error` |
| `docs/` | Documentation only | `docs/api-examples` |
| `test/` | Test-only changes | `test/optimizer-edge-cases` |
| `chore/` | Tooling, deps, housekeeping | `chore/ruff-config` |
| `release/` | Version bump and release prep | `release/v0.2.0` |

**Good:**

- `feature/simple-experiment`
- `fix/validation-null-input`
- `docs/git-versioning-guide`

**Bad:**

- `my-branch`
- `fix`
- `Feature_Parser`
- `wojciech-work`

## 2.4 Branch Lifecycle

1. Create branch from `main`.
2. Make small, focused commits on the branch.
3. Push the branch and open a PR.
4. Address review feedback with additional commits (or squash before merge, if the team agrees).
5. Merge into `main` after CI passes and review is approved.
6. Delete the branch after merge.

Keep branches short-lived. If a branch lives more than a few days, rebase or merge `main` into it regularly to avoid large conflicts.

```bash
# Update your branch with latest main
git checkout feature/parser
git fetch origin
git merge origin/main
```

---

# 3. Commits

## 3.1 One Logical Change

Each commit should represent a single, coherent change that could be reverted independently.

**Good — separate commits:**

```
Add tokenizer module
Add parser unit tests
Fix empty-input handling in parser
```

**Bad — mixed commits:**

```
Add parser, fix unrelated bug, update README, rename files
```

## 3.2 Commit Message Format

Use this structure:

```
<type>: <short summary>

[optional body — explain why, not just what]

[optional footer — issue references]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or behavior |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that is not a fix or feature |
| `chore` | Build, tooling, dependencies |
| `ci` | CI/CD configuration |

### Summary line rules

- Use imperative mood: **"Add parser"**, not "Added parser" or "Adds parser".
- Keep the summary under ~72 characters.
- Do not end with a period.
- Be specific enough that `git log --oneline` is useful.

### Examples

**Good:**

```
feat: add float genome representation

fix: handle empty population in optimizer engine

docs: add git and versioning guide

test: cover invalid genome bounds in float_genome

chore: bump ruff to 0.8.x
```

**Bad:**

```
Update
```

```
fixed stuff
```

```
@fix fixed import issues
```

```
Final version
```

```
WIP
```

## 3.3 When to Commit

Commit when:

- A small piece of work is complete and the code runs.
- Tests pass for the changed area.
- You are about to switch tasks or stop for the day.

Do not commit:

- Broken code (unless explicitly marked WIP on a private branch — avoid on shared branches).
- Generated artifacts, virtual environments, or secrets (`.env`, credentials).
- Unrelated changes bundled together.

## 3.4 Staging and Reviewing

Before committing, review what you are about to save:

```bash
git status
git diff
git add -p   # stage changes interactively
git commit -m "feat: add experiment builder"
```

---

# 4. Pull Requests

All changes reach `main` through pull requests.

## 4.1 PR Title

Use the same style as commit summaries:

```
feat: add simple experiment runner
fix: correct import path in optimizer engine
```

## 4.2 PR Description

Include:

1. **What changed** — brief summary of the diff.
2. **Why** — problem or motivation.
3. **How to test** — steps or commands for reviewers.

Example:

```markdown
## Summary
Add a minimal experiment runner for the optimizer engine.

## Motivation
We need an end-to-end path to evaluate genomes before adding GenAI helpers.

## Test plan
- [ ] `pytest tests/test_simple_experiment.py`
- [ ] Run example from README
```

## 4.3 PR Checklist

Before requesting review:

- [ ] Branch is up to date with `main`
- [ ] CI passes
- [ ] Tests added or updated for behavior changes
- [ ] Documentation updated if user-facing behavior changed
- [ ] `CHANGELOG.md` updated if this will be part of the next release
- [ ] No secrets or local-only files included
- [ ] Commit messages follow this guide

## 4.4 Merge Rules

- Require at least **one approving review**.
- Require **CI status checks** to pass.
- Prefer **squash merge** for feature branches with many small commits, **or** keep a clean commit history with rebase — pick one approach per PR and stay consistent.
- Delete the source branch after merge.

---

# 5. Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

## 5.1 When to Bump

| Change | Version bump | Example |
|--------|--------------|---------|
| Breaking API or behavior change | MAJOR | `0.1.0` → `1.0.0` |
| New backward-compatible feature | MINOR | `0.1.0` → `0.2.0` |
| Backward-compatible bug fix | PATCH | `0.2.0` → `0.2.1` |

While the project is at `0.x.y`, treat `MINOR` as the usual bump for new features and `PATCH` for fixes. A `1.0.0` release signals a stable, documented public API.

## 5.2 Where the Version Lives

The canonical version is in `pyproject.toml`:

```toml
[project]
version = "0.1.0"
```

Expose it from the package (e.g. `genai_opt.__version__`) so users and tests can read it.

Bump the version only on the branch that prepares a release — not on every feature PR.

## 5.3 Changelog

User-facing changes are recorded in [CHANGELOG.md](CHANGELOG.md) using [Keep a Changelog](https://keepachangelog.com/) format.

For each release, add a section:

```markdown
## [0.2.0] - 2026-07-15

### Added
- Simple experiment runner

### Fixed
- Import error in optimizer engine
```

Group entries under:

- `Added` — new features
- `Changed` — behavior changes that are not fixes
- `Deprecated` — soon-to-be removed APIs
- `Removed` — removed APIs
- `Fixed` — bug fixes
- `Security` — vulnerability fixes

Development decisions and narrative history belong in [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md), not in the changelog.

---

# 6. Releases and Tags

## 6.1 Release Checklist

Before tagging a release:

- [ ] All planned changes for this version are merged to `main`
- [ ] Full test suite passes locally and in CI
- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated with release date and entries
- [ ] README and docs reflect current usage
- [ ] PR reviewed and merged for the version bump (use `release/vX.Y.Z` branch if needed)

## 6.2 Creating a Tag

Tags mark immutable release points. Use annotated tags with a `v` prefix:

```bash
git checkout main
git pull origin main

# After version bump is merged
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

Tag name must match the version in `pyproject.toml` (with the `v` prefix).

## 6.3 Release Flow

```
feature branches
      |
      v
  Pull requests
      |
      v
     main  (CI green, reviewed)
      |
      v
 version bump + CHANGELOG  (release branch or direct PR)
      |
      v
   git tag vX.Y.Z
      |
      v
 GitHub Release (optional: attach artifacts, publish to PyPI)
```

For automated release steps, see the CD section in [cicd.md](cicd.md).

---

# 7. Common Scenarios

## Start a new feature

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
# ... work, commit, push ...
git push -u origin feature/my-feature
# Open PR on GitHub
```

## Fix a bug found on main

```bash
git checkout main
git pull origin main
git checkout -b fix/issue-description
# ... fix, add test, commit ...
git push -u origin fix/issue-description
```

## Prepare release 0.2.0

```bash
git checkout main
git pull origin main
git checkout -b release/v0.2.0
```

Update `pyproject.toml` version to `0.2.0` and finalize `CHANGELOG.md`, then:

```bash
git commit -m "chore: release v0.2.0"
git push -u origin release/v0.2.0
# Open PR, merge, then tag on main
```

---

# 8. What Not to Do

| Do not | Why |
|--------|-----|
| Commit directly to `main` | Bypasses review and CI |
| Force-push to `main` | Rewrites shared history and breaks teammates |
| Merge with failing CI | Breaks the stable branch |
| Use vague commit messages | Makes debugging and review harder |
| Bump version on every PR | Creates noisy releases and tag churn |
| Commit secrets or `.env` files | Security risk |
| Leave stale branches forever | Clutters the repository |

---

# 9. Quick Reference

## Branch naming

```
feature/<short-description>
fix/<short-description>
docs/<short-description>
release/v<major>.<minor>.<patch>
```

## Commit message

```
<type>: <imperative summary>
```

## Version format

```
MAJOR.MINOR.PATCH   (e.g. 0.2.1)
```

## Release tag

```
vMAJOR.MINOR.PATCH   (e.g. v0.2.1)
```

---

# Summary

```
Plan task
  → branch from main
  → small focused commits (typed messages)
  → push + pull request
  → CI + review
  → merge to main
  → bump version + CHANGELOG when releasing
  → tag vX.Y.Z
```

Consistent branching and versioning keep the project maintainable, reviewable, and safe to release.
