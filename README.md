# genai-opt
[![CI](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml/badge.svg)](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/genai-opt)](https://pypi.org/project/genai-opt/)
[![Python](https://img.shields.io/pypi/pyversions/genai-opt)](https://pypi.org/project/genai-opt/)

A Python library for GenAI optimization: an evolutionary engine for optimizing
anything you can score, including LLM prompts.

Requires Python 3.11 or newer, on Linux, macOS or Windows.

## Installation

```bash
pip install genai-opt
```

### From a checkout

```bash
git clone https://github.com/Wojciech151218/genai-opt.git
cd genai-opt

python3 -m venv .venv
source .venv/bin/activate        # Linux and macOS
# .venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -e ".[dev]"
pre-commit install
```

## Usage

```python
from experiments.simple_experiment import run_simple_experiment

population = run_simple_experiment(iterations=10, checkpoint_db=None)
best_genome, best_fitness = max(population.get_genome_fitness(), key=lambda item: item[1])
print(best_genome.phenotype, best_fitness)
```

Start with the [documentation](docs/index.md), including installation and a
step-by-step first experiment.

## Development

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

Preview or build documentation locally:

```bash
python -m mkdocs serve --dev-addr 127.0.0.1:8000
python -m mkdocs build --strict
```

## License

MIT — see [LICENSE](LICENSE).
