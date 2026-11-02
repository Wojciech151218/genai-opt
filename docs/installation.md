# Installation

Requires **Python 3.11 or newer** on Linux, macOS or Windows.

## Install the library

```bash
python -m pip install genai-opt
```

```python
import genai_opt

version: str = genai_opt.__version__
print(version)
#> 0.3.1
```

The installed package includes the library. To run the bundled examples,
including the [First Experiment](getting-started.md), use a repository checkout.

## Install from source

```bash
git clone https://github.com/Wojciech151218/genai-opt.git
cd genai-opt
```

=== "Windows PowerShell"

    ```powershell
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    ```

=== "Linux / macOS"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"
    ```

Use a Python 3.11+ interpreter. If PowerShell blocks activation, call
`.\.venv\Scripts\python.exe` directly instead.

## Preview documentation locally

From the repository root, with development dependencies installed:

```bash
python -m mkdocs serve --dev-addr 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/>. Markdown edits refresh the preview.
Keep the terminal running; press `Ctrl+C` to stop it.

```bash
python -m mkdocs build --strict
```

The build writes HTML to `site/`. Neither command publishes anything.
