from __future__ import annotations

import asyncio
import select
import sys
import termios
import tty
from datetime import datetime

from genai_opt.optimizer_engine.experiment_controller.experiment_controller import ExperimentController
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
    """Colored terminal logger for operations with pause/resume via ``p``."""

    def __init__(self, *, listen_for_pause: bool = True) -> None:
        super().__init__()
        self.listen_for_pause = listen_for_pause and sys.stdin.isatty()
        self._listener_task: asyncio.Task[None] | None = None
        self._last_phase: str | None = None

    async def setup(self) -> None:
        if self.listen_for_pause:
            self._listener_task = asyncio.create_task(self._listen_for_pause_key())

    async def control_iteration(self, iteration_metadata: IterationMetadata[P, Inv]) -> None:
        phase = self._infer_phase(iteration_metadata)
        for operation in iteration_metadata.operations:
            self._log_operation(operation)
        self._log_phase_summary(phase, iteration_metadata)
        self._last_phase = phase

    async def _listen_for_pause_key(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            key = await loop.run_in_executor(None, self._read_key_non_blocking)
            if key == "p":
                if self.is_paused():
                    self.resume()
                    self._print_system("resumed")
                else:
                    self.pause()
                    self._print_system("paused — press 'p' to resume")
            elif key == "q" and self.is_paused():
                self._print_system("quit requested while paused (engine keeps waiting)")
            await asyncio.sleep(0.05)

    @staticmethod
    def _read_key_non_blocking() -> str | None:
        if not sys.stdin.isatty():
            return None

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

    def _infer_phase(self, iteration_metadata: IterationMetadata[P, Inv]) -> str:
        kinds = {operation.kind for operation in iteration_metadata.operations}
        if kinds == {"invoke", "evaluate"} or kinds == {"evaluate"}:
            return "evaluate_population" if self._last_phase is None else "evaluate_offspring"
        if "crossover" in kinds:
            return "reproduce"
        if kinds == {"mutation"}:
            return "mutate"
        if "invoke" in kinds and "evaluate" in kinds and len(kinds) == 2:
            return "evaluate_offspring"
        return "evaluate_population"

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

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%H:%M:%S")
