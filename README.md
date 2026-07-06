# genai-opt
![Tests](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml/badge.svg)

A Python library for GenAI optimization.

## Installation

```bash
# Clone the repository
git clone https://github.com/Wojciech151218/genai-opt.git
cd genai-opt

# Create and activate a virtual environment (Python >= 3.13)
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1  # Windows

# Install the package with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Usage

```python
import genai_opt

print(genai_opt.__version__)
```

## Development

See [dev-guide.md](dev-guide.md) for the development workflow and [git-versioning-guide.md](git-versioning-guide.md) for branching, commits, and releases.

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

## License

MIT — see [LICENSE](LICENSE).
