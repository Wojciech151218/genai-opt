# Simple CI/CD Setup Tutorial

## Purpose

This guide explains how to add a simple Continuous Integration (CI) pipeline to a Python project using GitHub Actions.

The goal is to automatically:

- Run tests
- Check code quality
- Verify that new changes do not break the project

This setup is intentionally simple and suitable for small open-source projects and academic projects.

---

# 1. What is CI/CD?

## Continuous Integration (CI)

CI automatically checks code whenever changes are pushed.

Example:

A developer creates a pull request.

The CI system:

1. Downloads the code
2. Installs dependencies
3. Runs tests
4. Checks formatting/style
5. Reports success or failure


## Continuous Delivery (CD)

CD automates preparing releases.

Example:

When a version tag is created:

```
v0.1.0
```

The system can:

- Build the package
- Create a release
- Publish to package repositories


For this project we start with CI.

---

# 2. Requirements

You need:

- A GitHub repository
- Python project
- Tests
- Git installed


Example project:

```
project/

src/
tests/

pyproject.toml
README.md
```

---

# 3. Create GitHub Actions Folder

Create:

```
.github/workflows/
```

Structure:

```
project/

.github/
    workflows/
        tests.yml
```

GitHub automatically detects workflows inside this folder.

---

# 4. Create CI Workflow

Create:

```
.github/workflows/tests.yml
```

Add:

```yaml
name: Tests

on:
  push:
    branches:
      - main

  pull_request:


jobs:

  test:

    runs-on: ubuntu-latest


    steps:

      - name: Checkout repository
        uses: actions/checkout@v4


      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"


      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"


      - name: Run tests
        run: |
          pytest --cov=src/genai_opt --cov-report=term-missing


      - name: Check code style
        run: |
          ruff check .

      - name: Check formatting
        run: |
          ruff format --check .
```

---

# 5. Commit the Workflow

Add:

```bash
git add .github/workflows/tests.yml
```

Commit:

```bash
git commit -m "Add CI pipeline"
```

Push:

```bash
git push
```

---

# 6. Check the Result

Open your GitHub repository.

Go to:

```
Actions
```

You should see:

```
Tests
```

The workflow should start automatically.

A successful run means:

- Project installs correctly
- Tests pass
- Code style checks pass

---

# 7. Add CI Badge

Add to README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/actions/workflows/tests.yml/badge.svg)
```

Example:

```
README.md

Project status:

[CI Badge]
```

---

# 8. Protect Main Branch

Recommended for teams.

GitHub:

Repository Settings

→ Branches

→ Branch protection rules

Enable:

- Require pull request before merging
- Require status checks to pass


Now broken code cannot enter main.

---

# 9. Optional: Multiple Python Versions

To test compatibility:

Replace:

```yaml
python-version: "3.12"
```

with:

```yaml
strategy:
  matrix:
    python-version:
      - "3.10"
      - "3.11"
      - "3.12"


steps:

- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
```

Now tests run on three Python versions.

---

# 10. Optional: Add Formatting Check

Install:

```bash
pip install ruff
```

Format locally:

```bash
ruff format .
```

Check:

```bash
ruff format --check .
```

Add to workflow:

```yaml
- name: Check formatting
  run: ruff format --check .
```

---

# 11. Advanced Quality Checks

We use `pre-commit` and `Dependabot` to catch issues before CI even runs, and to keep dependencies updated.

## Pre-commit

Installs git hooks to run `ruff` on every commit automatically:

```bash
pre-commit install
```

## Dependabot

A `.github/dependabot.yml` file is used to automatically check for Python package updates weekly and create Pull Requests.

---

# 12. Simple CD Release Setup

When ready to publish:

Create a version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

A CD workflow can then:

- Build package
- Upload release files
- Publish to PyPI


Example flow:

```
Code
 |
 v
Pull Request
 |
 v
CI Tests
 |
 v
Merge
 |
 v
Version Tag
 |
 v
Release
```

---

# Team Rules

For this project:

Before merging:

- CI must pass
- Tests must pass
- At least one person reviews the code
- Documentation is updated if needed


---

# Troubleshooting

## Tests fail locally but work in CI

Check:

- Python version
- Missing dependencies
- Environment differences


## CI cannot install package

Check:

- pyproject.toml exists
- Package structure is correct


## Workflow does not start

Check:

- File is inside `.github/workflows`
- YAML indentation is correct


---

# Summary

A minimal professional workflow:

Developer
↓
Feature branch
↓
Pull Request
↓
GitHub Actions:
- Install
- Test
- Lint
↓
Review
↓
Merge


This provides a reliable foundation for maintaining an open-source quality project.