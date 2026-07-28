from __future__ import annotations

import asyncio
import contextlib
import sys
from datetime import datetime

from genai_opt.optimizer_engine.engine_state import IterationPhase
from genai_opt.optimizer_engine.experiment_controller.experiment_controller import ExperimentController
from genai_opt.optimizer_engine.experiment_controller.key_reader import KeyReader, create_key_reader
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation, OperationKind
from genai_opt.optimizer_engine.utils.typevars import Inv, P

_RESET = "\033[0m"
_DIM = "\033[90m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"

_KIND_COLORS: dict[OperationKind, str] = {
    "invoke": _CYAN,
    "evaluate": _GREEN,
    "mutation": _MAGENTA,
    "crossover": _BLUE,
    "unknown": _DIM,
}


class TerminalController(ExperimentController):
    """Colored terminal logger for operations with pause/resume via ``p``.

    Key handling is delegated to a :class:`KeyReader`, so this works on POSIX
    and Windows and degrades to log-only output when stdin is not a terminal.

    Args:
        listen_for_pause: Whether to watch for the pause key. Forced off when
            the selected reader cannot deliver keypresses, so reading this
            attribute always tells you whether pausing is actually available.
        key_reader: Reader to use instead of the platform default. Mainly for
            tests and for embedding in other frontends.
    """

    def __init__(self, *, listen_for_pause: bool = True, key_reader: KeyReader | None = None) -> None:
        super().__init__()
        self._key_reader = key_reader or create_key_reader()
        self.listen_for_pause = listen_for_pause and self._key_reader.can_read_keys
        self._listener_task: asyncio.Task[None] | None = None
        self._reader_open = False

    async def setup(self) -> None:
        if not self.listen_for_pause:
            return

        self._key_reader.open()
        self._reader_open = True
        self._listener_task = asyncio.create_task(self._listen_for_pause_key(self._key_reader))

    async def teardown(self) -> None:
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None

        if self._reader_open:
            self._key_reader.close()
            self._reader_open = False

    async def control_iteration(self, iteration_metadata: IterationMetadata[P, Inv]) -> None:
        phase = iteration_metadata.phase.value if iteration_metadata.phase is not None else "unknown"
        self._log_phase_summary(phase, iteration_metadata)

    async def control_operation(self, iteration: int, phase: IterationPhase, operation: Operation) -> None:
        self._log_operation(operation)

    async def _listen_for_pause_key(self, reader: KeyReader) -> None:
        loop = asyncio.get_running_loop()
        while True:
            key = await loop.run_in_executor(None, reader.read_key)
            self._handle_key(key)
            await asyncio.sleep(0)

    def _handle_key(self, key: str | None) -> None:
        if key == "p":
            if self.is_paused():
                self.resume()
                self._print_system("resumed")
            else:
                self.pause()
                self._print_system("paused — press 'p' to resume")
        elif key == "q" and self.is_paused():
            self._print_system("quit requested while paused (engine keeps waiting)")

    def _log_phase_summary(self, phase: str, iteration_metadata: IterationMetadata[P, Inv]) -> None:
        fitnesses = [state.fitness for state in iteration_metadata.phenotype_states if state.fitness is not None]
        population_size = len(iteration_metadata.phenotype_states)
        timestamp = self._timestamp()

        fitness_summary = "population=0"
        if fitnesses:
            fitness_summary = (
                f"population={population_size} "
                f"best={max(fitnesses):.4f} worst={min(fitnesses):.4f} mean={sum(fitnesses) / len(fitnesses):.4f}"
            )

        paused = f" {_YELLOW}PAUSED{_RESET}" if self.is_paused() else ""
        print(
            f"{_DIM}[{timestamp}]{_RESET} "
            f"{_GREEN}──▶{_RESET} {phase} "
            f"iteration={iteration_metadata.iteration} "
            f"{fitness_summary} "
            f"ops={len(iteration_metadata.operations)} "
            f"tokens={iteration_metadata.total_tokens} "
            f"cost=${iteration_metadata.total_cost:.6f} "
            f"{iteration_metadata.total_duration_seconds:.4f}s"
            f"{paused}"
        )

    def _log_operation(self, operation: Operation) -> None:
        timestamp = self._timestamp()
        kind_color = _KIND_COLORS.get(operation.kind, _DIM)
        model = operation.llm_metadata.model if operation.llm_metadata else "-"
        short_id = str(operation.id)[:8]

        print(
            f"{_DIM}[{timestamp}]{_RESET}   "
            f"{kind_color}{operation.kind:<9}{_RESET} "
            f"tokens={_YELLOW}{operation.tokens:<6}{_RESET} "
            f"{operation.duration_seconds:.4f}s "
            f"model={_DIM}{model}{_RESET} "
            f"id={short_id}"
        )

    def _print_system(self, message: str) -> None:
        print(f"{_BOLD}{_YELLOW}[genai-opt]{_RESET} {message}")
        sys.stdout.flush()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%H:%M:%S")
