import asyncio
import json

import websockets

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.experiment_controller.websocket_controller import WebSocketExperimentController
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation


def test_websocket_controller_broadcasts_iteration() -> None:
    async def run_test() -> None:
        controller = WebSocketExperimentController(port=0)  # OS picks free port
        await controller.setup()

        # Grab the actual port bound
        port = controller._server.sockets[0].getsockname()[1]

        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            metadata = IterationMetadata(iteration=1)
            metadata.phase = IterationPhase.MUTATE
            await controller.control_iteration(metadata)

            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            data = json.loads(response)
            assert data["type"] == "iteration"
            assert data["iteration"] == 1
            assert data["phase"] == IterationPhase.MUTATE.value

        await controller.teardown()

    asyncio.run(run_test())


def test_websocket_controller_broadcasts_operation() -> None:
    async def run_test() -> None:
        controller = WebSocketExperimentController(port=0)
        await controller.setup()
        port = controller._server.sockets[0].getsockname()[1]

        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            op = Operation(value="some_value", kind="test", duration_seconds=1.5)
            await controller.control_operation(iteration=2, phase=IterationPhase.REPRODUCE, operation=op)

            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            data = json.loads(response)
            assert data["type"] == "operation"
            assert data["iteration"] == 2
            assert data["phase"] == IterationPhase.REPRODUCE.value
            assert data["operation_kind"] == "test"

        await controller.teardown()

    asyncio.run(run_test())


def test_websocket_controller_pause_resume() -> None:
    async def run_test() -> None:
        controller = WebSocketExperimentController(port=0)
        await controller.setup()
        port = controller._server.sockets[0].getsockname()[1]

        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            # Client sends pause command
            await websocket.send(json.dumps({"command": "pause"}))

            # Wait for the server to confirm it is paused
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            assert json.loads(response)["status"] == "paused"
            assert controller.is_paused() is True

            # Client sends resume command
            await websocket.send(json.dumps({"command": "resume"}))

            # Wait for resume confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            assert json.loads(response)["status"] == "running"
            assert controller.is_paused() is False

        await controller.teardown()

    asyncio.run(run_test())
