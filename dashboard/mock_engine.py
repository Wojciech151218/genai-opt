"""Mock WebSocket engine for dashboard development without a real experiment."""

from __future__ import annotations

import asyncio
import json
import random

import websockets


HOST = "localhost"
PORT = 8765
POPULATION_SIZE = 20
PHASES = ["SELECTION", "CROSSOVER", "MUTATION", "EVALUATION"]
OPERATION_KINDS = ["evaluate_haiku", "llm_generate_haiku", "llm_mutate_haiku"]


def _population_json() -> list[dict[str, object]]:
    return [
        {
            "id": f"genome_{i}",
            "phenotype": f"Haiku variant #{i}",
            "fitness": round(random.uniform(50, 100), 2),
        }
        for i in range(POPULATION_SIZE)
    ]


async def _handle_pause(websocket: object) -> None:
    await websocket.send(json.dumps({"type": "status", "status": "paused"}))
    while True:
        resume_msg = await websocket.recv()
        if json.loads(resume_msg).get("command") == "resume":
            await websocket.send(json.dumps({"type": "status", "status": "running"}))
            return


async def mock_engine(websocket: object) -> None:
    print("Dashboard connected!")
    await websocket.send(json.dumps({"type": "status", "status": "running"}))

    iteration = 1
    try:
        while True:
            phase = random.choice(PHASES)
            await websocket.send(
                json.dumps(
                    {
                        "type": "iteration",
                        "iteration": iteration,
                        "population_size": POPULATION_SIZE,
                        "phase": phase,
                        "population_json": _population_json(),
                    }
                )
            )

            for _ in range(random.randint(2, 4)):
                await asyncio.sleep(0.5)
                await websocket.send(
                    json.dumps(
                        {
                            "type": "operation",
                            "iteration": iteration,
                            "phase": phase,
                            "operation_kind": random.choice(OPERATION_KINDS),
                            "duration": random.uniform(0.5, 3.5),
                        }
                    )
                )

            iteration += 1
            await asyncio.sleep(1)

            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                data = json.loads(msg)
                if data.get("command") == "pause":
                    await _handle_pause(websocket)
            except TimeoutError:
                pass

    except Exception as exc:
        print(f"Disconnected: {exc}")


async def main() -> None:
    print(f"Starting mock WebSocket server on ws://{HOST}:{PORT}")
    print("Haiku experiment simulation active. Open http://localhost:5173")
    async with websockets.serve(mock_engine, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
