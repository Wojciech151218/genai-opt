# Web Dashboard (Liquid Glass)

The Web Dashboard is an interactive React application used to monitor and control active evolutionary optimization runs in real time as well as inspect historical experiments stored in SQLite checkpoint databases.

## Architecture & Technology

The dashboard resides in the `dashboard/` directory and connects to two lightweight local Python services:
- **React + Vite**: Component-driven UI with fast development HMR and `/api` proxy support.
- **Native WebSockets (`ws://localhost:8765`)**: Two-way telemetry and control channel (`pause` / `resume`) powered by `WebSocketExperimentController`.
- **SQLite History HTTP API (`http://localhost:8766/api`)**: Zero-dependency read-only JSON server (`DashboardAPIServer`) exposing `.checkpoints/*.db` history.
- **Lucide React**: Scalable vector icons with Dark and Light theme support.

## Views & Capabilities

### 1. Live Monitor
- **Engine Controls**: Pause (`pausing` -> `paused`) and resume active optimization runs safely between phases/operations.
- **Live Telemetry**: Displays active iteration, population size, and human-readable phase names.
- **Structured Population Cards**: Renders each genome's `Fitness` badge, formatted `Phenotype (JSON)`, and `Invocation Output` live.
- **Operations Feed**: Streams individual genome/LLM operations and execution durations.

### 2. Database Explorer
- **Database & Experiment Discovery**: Automatically lists `.db` files in `.checkpoints/` (or accepts a custom SQLite file path) and summarizes stored experiments (`Peak Fitness`, `Total Tokens`, checkpoint count).
- **Checkpoints Timeline**: Chronological phase-by-phase history with fitness highlights and timestamps.
- **Saved Population & Offspring Inspection**: Displays step-level metrics (`Best / Mean / Worst Fitness`, `Step Tokens`, `Duration`) and lets you switch between `Parents` and `Offspring` snapshots.
- **Phase Operations**: Lists recorded LLM operations with model names and `tokens_in` / `tokens_out` breakdowns.

## Running the Dashboard

### Automatically with an Experiment
Call `.start_dashboard()` on `ExperimentBuilder` so `Engine.run()` starts and stops both the Vite UI and the SQLite History API automatically:
```python
builder = build_haiku_experiment(llm)
builder.start_dashboard()
engine = builder.build().from_checkpoint()
await engine.run()
```

### Standalone Mode (Browsing Saved Databases Without Running an Engine)
Launch the dashboard and SQLite History API server directly without invoking any LLM calls:
```bash
PYTHONPATH=src python3 -m genai_opt.optimizer_engine.dashboard
```
Then open `http://localhost:5173` in your browser.
