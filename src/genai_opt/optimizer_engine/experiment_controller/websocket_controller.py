import asyncio
import json
from typing import Any

import websockets

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.experiment_controller.experiment_controller import ExperimentController
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation


class WebSocketExperimentController(ExperimentController):
    """Experiment controller that provides two-way WebSocket communication.

    Broadcasts iteration and operation states to connected UI clients,
    and listens for 'pause' / 'resume' commands to steer the experiment.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        super().__init__()
        self.host = host
        self.port = port
        self._clients: set[Any] = set()
        self._server = None
        self._resume_event = asyncio.Event()
        self._resume_event.set()

    def pause(self) -> None:
        super().pause()
        self._resume_event.clear()

    def resume(self) -> None:
        super().resume()
        self._resume_event.set()

    async def setup(self) -> None:
        """Initialize the WebSocket server."""
        self._server = await websockets.serve(self._handler, self.host, self.port)

    async def teardown(self) -> None:
        """Shutdown the WebSocket server."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handler(self, websocket: Any) -> None:
        self._clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    cmd = data.get("command")
                    if cmd == "pause":
                        self.pause()
                        await self._broadcast({"type": "status", "status": "paused"})
                    elif cmd == "resume":
                        self.resume()
                        await self._broadcast({"type": "status", "status": "running"})
                except json.JSONDecodeError:
                    pass
        finally:
            self._clients.remove(websocket)

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        if not self._clients:
            return
        msg = json.dumps(payload)
        await asyncio.gather(*(client.send(msg) for client in self._clients), return_exceptions=True)

    async def _wait_if_paused(self) -> None:
        if self.is_paused():
            await self._resume_event.wait()

    async def control_iteration(self, iteration_metadata: IterationMetadata) -> None:
        await self._broadcast(
            {
                "type": "iteration",
                "iteration": iteration_metadata.iteration,
                "phase": iteration_metadata.phase.value if iteration_metadata.phase else None,
                "population_size": len(iteration_metadata.phenotype_states),
            }
        )
        await self._wait_if_paused()

    async def control_operation(self, iteration: int, phase: IterationPhase, operation: Operation) -> None:
        await self._broadcast(
            {
                "type": "operation",
                "iteration": iteration,
                "phase": phase.value,
                "operation_kind": operation.kind,
                "duration": operation.duration_seconds,
            }
        )
        await self._wait_if_paused()
