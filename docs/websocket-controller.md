# WebSocket Experiment Controller

The `WebSocketExperimentController` enables two-way real-time communication between the evolutionary algorithm engine and external clients (such as a web UI).

## Overview

The controller binds to `localhost:8765` by default and reports phase and
operation updates to connected clients. Pass it as the
`experiment_controller` when building an experiment.

!!! warning "Local use"
    The controller does not provide authentication or TLS by default. Keep
    it bound to localhost unless you secure access separately.

## Protocol and Models

Messages passed between the client and server follow a structured JSON schema, strictly validated by Pydantic.

### Server Messages (Broadcasted)
- **Status Message**: The format supports running, paused, and stopped. The
  controller currently broadcasts paused and running in response to commands.
  - JSON format: `{"type": "status", "status": "running|paused|stopped"}`
- **Iteration Message**: Reports metadata for a completed phase, including a population snapshot when provided.
  - JSON example: `{"type": "iteration", "iteration": 1, "phase": "mutate", "population_size": 10, "population_json": []}`
- **Operation Message**: Dispatched for atomic algorithmic events.
  - JSON example: `{"type": "operation", "iteration": 1, "phase": "reproduce", "operation_kind": "crossover", "duration": 0.05}`

### Client Messages (Received)
- **Command Message**: Used to remotely steer the optimization process.
  - JSON format: `{"command": "pause"}` or `{"command": "resume"}`

The controller acknowledges pause immediately, then waits at the next phase
or operation callback. It does not cancel work already executing.
