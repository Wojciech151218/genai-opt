# WebSocket Experiment Controller

The `WebSocketExperimentController` enables two-way real-time communication between the evolutionary algorithm engine and external clients (such as a web UI).

## Overview

The controller binds a WebSocket server on a specified port (default: 8765) and manages active clients. It intercepts engine state changes and broadcasts them securely using rigorously typed Pydantic models.

## Protocol and Models

Messages passed between the client and server follow a structured JSON schema, strictly validated by Pydantic.

### Server Messages (Broadcasted)
- **Status Message**: Dispatched when the engine pauses, resumes, or stops.
  - JSON format: `{"type": "status", "status": "running|paused|stopped"}`
- **Iteration Message**: Dispatched when a new generation starts.
  - JSON format: `{"type": "iteration", "iteration": 1, "phase": "MUTATE", "population_size": 10}`
- **Operation Message**: Dispatched for atomic algorithmic events.
  - JSON format: `{"type": "operation", "iteration": 1, "phase": "REPRODUCE", "operation_kind": "crossover", "duration": 0.05}`

### Client Messages (Received)
- **Command Message**: Used to remotely steer the optimization process.
  - JSON format: `{"command": "pause"}` or `{"command": "resume"}`
