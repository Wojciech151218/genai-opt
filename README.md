# genai-opt
[![CI](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml/badge.svg)](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml)
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
from genai_opt.experiments.simple_experiment import run_simple_experiment

population = run_simple_experiment(iterations=10, checkpoint_dir=None)
best_genome, best_fitness = max(population.get_genome_fitness(), key=lambda item: item[1])
print(best_genome.phenotype, best_fitness)
```

See the [documentation](docs/index.md) for building experiments from parts,
writing your own genome, resuming from checkpoints, and optimizing LLM prompts.

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

Build documentation locally:

```bash
mkdocs build
```

## License

MIT — see [LICENSE](LICENSE).
