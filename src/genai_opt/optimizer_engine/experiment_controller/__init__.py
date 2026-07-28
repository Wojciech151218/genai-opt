"""Live observation and control of a running experiment.

A controller receives every phase and every individual operation as it happens,
and can pause the run. :class:`TerminalController` is the built-in
implementation; the key reader backends let it work on POSIX and Windows and
degrade gracefully when stdin is not a terminal.
"""

from genai_opt.optimizer_engine.experiment_controller.experiment_controller import (
    ExperimentController,
    NullExperimentController,
)
from genai_opt.optimizer_engine.experiment_controller.key_reader import (
    KeyReader,
    NullKeyReader,
    PosixKeyReader,
    WindowsKeyReader,
    create_key_reader,
)
from genai_opt.optimizer_engine.experiment_controller.terminal_controller import TerminalController

__all__ = [
    "ExperimentController",
    "KeyReader",
    "NullExperimentController",
    "NullKeyReader",
    "PosixKeyReader",
    "TerminalController",
    "WindowsKeyReader",
    "create_key_reader",
]
