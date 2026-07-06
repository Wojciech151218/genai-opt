# genai-opt
![Tests](https://github.com/Wojciech151218/genai-opt/actions/workflows/tests.yml/badge.svg)

A Python library for GenAI optimization.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
import genai_opt

print(genai_opt.__version__)
```

## Development

See [dev-guide.md](dev-guide.md) for the development workflow and [git-versioning-guide.md](git-versioning-guide.md) for branching, commits, and releases.

Run tests:

```bash
pytest
```

Check code style:

```bash
ruff check .
```

## License

MIT — see [LICENSE](LICENSE).
