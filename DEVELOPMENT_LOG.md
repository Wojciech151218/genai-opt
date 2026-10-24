# Development Log

This log records development history, decisions, problems, and solutions for
academic evaluation and team collaboration.

---

## 2026-07-01 — Initial scaffold

**Goal:** Create the initial project structure.

**Completed:**

- Set up `src/genai_opt/` package layout
- Added placeholder modules, tests, and documentation files
- Configured `pyproject.toml` for installation and development

**Notes:**

- Scaffold follows the structure defined in [dev-guide.md](dev-guide.md).

---

## 2026-07-06 - Initial MkDocs documentation

**Goal:** Add the first local documentation site for the project.

**Completed:**

- Added `mkdocs.yml`
- Added initial documentation pages in `docs/`
- Documented installation, usage, API overview, and development workflow
- Verified the documentation with `mkdocs build`

**Notes:**

- This is the first documentation scaffold and can be expanded as the public
  API stabilizes.

---

## 2026-07-29 - Database Checkpointer Implementation

**Goal:** Implement persistent database storage for experiment checkpoints.

**Completed:**

- Created `SqliteCheckpointer` class inheriting from base `Checkpointer`.
- Implemented `save_checkpoint` and `load` methods using relational database queries.
- Created `test_database_checkpointer.py` ensuring full TDD coverage.

**Problem:**
Needed robust persistent database storage without violating the "no unnecessary dependencies" rule.

**Solution:**
Used the standard library's `sqlite3` module to implement a lightweight, zero-configuration local SQL database.

---

## 2026-08-02 - WebSocket Controller and Web Dashboard Scaffold

**Goal:** Enable real-time monitoring and interactive control (`pause` / `resume`) of evolutionary experiments from a web browser.

**Completed:**

- Implemented `WebSocketExperimentController` and Pydantic message schemas (`ServerStatusMessage`, `ServerIterationMessage`, `ServerOperationMessage`, `ClientCommandMessage`).
- Scaffolded the React + Vite web dashboard (`dashboard/`) with a liquid-glass dark UI inspired by macOS and iOS systems theme, live iteration metrics, operation feed, and WebSocket connection state indicators.
- Added MkDocs documentation pages for `SqliteCheckpointer`, `WebSocketExperimentController`, and the Web Dashboard.
- Added unit tests for `WebSocketExperimentController` (`tests/unit/test_websocket_controller.py`).

**Problem:**
Pausing an asynchronous evolutionary loop from an external UI without blocking or corrupting ongoing LLM operations.

**Solution:**
Used an `asyncio.Event` (`_resume_event`) inside `WebSocketExperimentController` that gates phase and operation transitions cleanly between steps while broadcasting status updates to connected clients.

---

## 2026-09-05 - Web Dashboard Enhancements and Builder Integration

**Goal:** Improve dashboard usability, add light/dark theme support and population inspection, and integrate UI process management directly into `ExperimentBuilder`.

**Completed:**

- Localized the dashboard interface to English and mapped internal operation/phase identifiers (e.g., `evaluate_offspring`) to human-readable labels.
- Added an intermediate `pausing` UI state so users get immediate visual feedback while the engine finishes its current operation before pausing.
- Implemented a light/dark theme toggle using CSS custom properties (`[data-theme="light"]`).
- Added a `Population State` panel to inspect genome states per iteration.
- Added `start_dashboard()` to `ExperimentBuilder` and `Engine`, automatically managing the Vite dev server subprocess lifecycle in `Engine.run()` via a `finally` block.

**Problem:**
Placing `dashboard.py` inside `genai_opt.experiments` caused circular imports when `Engine` and `ExperimentBuilder` needed to manage the UI process.

**Solution:**
Moved `dashboard.py` into `genai_opt.optimizer_engine`, allowing `Engine.run()` to start and stop the UI subprocess cleanly without circular dependencies.

---

## 2026-10-19 - Full Branch Integration, Structured Population Cards, and Responsive UI Fixes

**Goal:** Integrate the checkpointer, WebSocket controller, and web dashboard branches, stream live population states from the engine, and polish the UI layout for real LLM experiments.

**Completed:**

- Merged `feature/sqlite-checkpointer`, `feature/websocket-controller`, and `feature/experiment-web-dashboard` and exported `SqliteCheckpointer` and `WebSocketExperimentController` in `genai_opt.optimizer_engine`.
- Added `teardown()` to `ExperimentController` and ensured `Engine.run()` closes the WebSocket server in its `finally` block.
- Extended `ServerIterationMessage` and `WebSocketExperimentController.control_iteration()` to serialize and broadcast `population_json` (filtering out internal LangChain LLM client objects from `SimpleSystemPromptPhenotype` for clean display).
- Rebuilt the `Population State` panel into structured genome cards (header with genome ID and `Fitness` badge, formatted JSON block for `phenotype`, and `Invocation Output` preview).
- Fixed responsive CSS grid layout in `dashboard/src/index.css` so panels and the `Active Phase` card scale cleanly without overflowing when the browser window shrinks.
- Verified all 78 unit, integration, and edge-case tests pass with `pytest` and formatted the codebase with `ruff`.

**Problem:**

1. Running multiple experiments sequentially in tests failed with `OSError: [Errno 48] address already in use` on port `8765`, and `SqliteCheckpointer` failed if `.checkpoints/` did not exist yet.
2. Shrinking the browser window caused the `Active Phase` metric card and fixed `350px` grid columns to overflow outside the main dashboard frame.

**Solution:**

1. Added `await self.experiment_controller.teardown()` to `Engine.run()`'s `finally` block and automatic parent directory creation in `SqliteCheckpointer._init_db()`.
2. Replaced fixed grid widths with fluid `minmax(...)` tracks, added `min-width: 0` / `overflow: hidden` containment on panels, responsive font sizing (`clamp(...)`), and `@media` breakpoints for smaller viewports.

---

## 2026-10-23 - SQLite Database Explorer and Standalone Dashboard Mode

**Goal:** Extend the web dashboard beyond live WebSocket monitoring so users can browse historical experiments, checkpoint timelines, populations, and LLM operation logs stored in SQLite databases.

**Completed:**

- Extended `SqliteCheckpointer` with Pydantic history records (`GenomeSnapshotRecord`, `ExperimentSummaryRecord`, `CheckpointSummaryRecord`, `CheckpointDetailRecord`) and query methods (`list_experiments()`, `list_checkpoints()`, `get_checkpoint()`).
- Implemented `DashboardAPIServer` (`dashboard_api.py`) using Python's built-in `http.server` to serve read-only JSON endpoints (`/api/databases`, `/api/experiments`, `/api/checkpoints`, `/api/checkpoints/<id>`) without external dependencies.
- Integrated `DashboardAPIServer` lifecycle into `dashboard.py`, added a standalone CLI entry point (`python -m genai_opt.optimizer_engine.dashboard`), and configured `/api` proxying in `dashboard/vite.config.js`.
- Built the `DatabaseExplorer` React view and top navigation tabs (`Live Monitor` / `Database Explorer`) supporting both dark and light themes, parent/offspring population switching, and operation token breakdowns.
- Added unit tests for `SqliteCheckpointer` history queries and `DashboardAPIServer` endpoints, and updated MkDocs documentation.

**Problem:**
Browser applications cannot read local `.checkpoints/*.db` SQLite files directly, and instantiating `Population.from_json()` for arbitrary historical experiments would require runtime `restore_context` callables and live LLM instances.

**Solution:**
Parsed stored `CheckpointPayloadRecord` and `IterationMetadataRecord` JSON directly inside `SqliteCheckpointer` (stripping internal LangChain `llm` client objects) and exposed them through a lightweight stdlib `ThreadingHTTPServer` proxied by Vite.

---

## 2026-10-23 - Dual UI Design System: Liquid Glass and Modern Developer

**Goal:** Add a clean, distraction-free analytical workspace style alongside Liquid Glass for users who prefer utilitarian developer interfaces similar to Google Colab, Google Drive, and TensorBoard.

**Completed:**

- Added a persistent `uiStyle` (`glass` | `modern`) switcher in `App.jsx` synchronized with `<html data-style="...">` and `localStorage` alongside the `dark` / `light` theme toggle.
- Created `dashboard/src/modern-developer.css` implementing a full-bleed workspace layout, flat Material/Workspace surfaces, hairline borders, `JetBrains Mono` code cells, and dark/light palettes without decorative background orbs or blur filters.
- Updated `docs/web-dashboard.md` to document all four style and theme combinations.

**Problem:**
Decorative glassmorphism effects (animated background orbs, heavy backdrop blur, floating margins) can feel visually busy or distracting during long analytical sessions.

**Solution:**
Scoped the alternative workspace aesthetic cleanly under `[data-style="modern"]` CSS custom properties and layout overrides in a dedicated stylesheet (`modern-developer.css`), preserving `Liquid Glass` intact while offering one-click switching.
