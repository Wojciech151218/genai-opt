# Web Dashboard

The Web Dashboard is an interactive React application used to monitor and control active evolutionary optimization runs in real time as well as inspect historical experiments stored in SQLite checkpoint databases.

## Architecture & Technology

The dashboard resides in the `dashboard/` directory and connects to two lightweight local Python services:

- **React + Vite**: Component-driven UI with fast development HMR and `/api` proxy support.
- **Native WebSockets (`ws://localhost:8765`)**: Two-way telemetry and control channel (`pause` / `resume`) powered by `WebSocketExperimentController`.
- **SQLite History HTTP API (`http://localhost:8766/api`)**: Zero-dependency read-only JSON server (`DashboardAPIServer`) exposing `.checkpoints/*.db` history.
- **Lucide React**: Scalable vector icons.

## Interface Styles & Themes

The header lets you switch between the Liquid Glass and Modern Developer
layouts and between light and dark themes. Preferences are stored locally in
the browser.

## Views & Capabilities

### 1. Live Monitor

- **Engine Controls**: Request pause or resume for the connected run. A pause does not cancel work in the current phase.
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

From a source checkout with Node.js and npm installed, run the bundled numeric
demo with its dashboard enabled:

```bash
python -m experiments.simple_experiment
```

For your own experiment, configure a `WebSocketExperimentController` and call
`builder.start_dashboard()` before `builder.build().run()`. The dashboard
process and SQLite history API run alongside the experiment. The numeric
example can finish before you have time to open the live view; use standalone
mode to browse its saved checkpoints afterward.

### Standalone Mode (Browsing Saved Databases Without Running an Engine)

Launch the dashboard and SQLite History API server directly without invoking any LLM calls:

```bash
python -m genai_opt.optimizer_engine.dashboard
```

Then open `http://localhost:5173` in your browser.

## Mock engine (no real experiment)

To exercise the UI without running an LLM-backed experiment, start the mock WebSocket server in a second terminal:

```bash
python dashboard/mock_engine.py
```

It listens on `ws://localhost:8765` and streams fake iteration / operation / population telemetry, including pause and resume.
