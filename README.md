# genai-opt
![Tests](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/genai-opt.svg)](https://pypi.org/project/genai-opt/)

A Python library for GenAI optimization.

## Installation

```bash
pip install genai-opt
```

Requires Python >= 3.13.

## Usage

```python
import genai_opt

print(genai_opt.__version__)
```

## Development

```bash
git clone https://github.com/Wojciech151218/genai-opt.git
cd genai-opt

# Create and activate a virtual environment (Python >= 3.13)
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Install the package with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branching, commits, PRs, versioning, and releases.

This project uses modern Python tooling:
- **Ruff**: For lightning-fast linting and formatting.
- **Pre-commit**: To ensure code quality before every commit.
- **Pytest**: For testing and code coverage.
- **Dependabot**: For automated dependency updates.

### Running tests with coverage:

```bash
pytest --cov=src/genai_opt --cov-report=term-missing
```

### Checking code style manually:

```bash
ruff check .
ruff format --check .
```

Build documentation locally:

```bash
mkdocs build
```

## License

MIT — see [LICENSE](LICENSE).
