"""Tests for the platform-agnostic terminal controller and its key readers."""

import asyncio
import subprocess
import sys
import time

import pytest

from genai_opt.optimizer_engine.experiment_controller.key_reader import (
    KeyReader,
    NullKeyReader,
    PosixKeyReader,
    WindowsKeyReader,
    create_key_reader,
    stdin_is_interactive,
)
from genai_opt.optimizer_engine.experiment_controller.terminal_controller import TerminalController


class _ScriptedKeyReader(KeyReader):
    """Replays a fixed sequence of keys, then reports nothing forever."""

    def __init__(self, keys: list[str | None]) -> None:
        super().__init__(poll_interval=0.0)
        self.keys = list(keys)
        self.opened = 0
        self.closed = 0

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def read_key(self) -> str | None:
        if self.keys:
            return self.keys.pop(0)
        return None


def _pretend_tty(monkeypatch, *, interactive: bool) -> None:
    class _Stdin:
        def isatty(self) -> bool:
            return interactive

        def fileno(self) -> int:
            return 0

    monkeypatch.setattr(sys, "stdin", _Stdin())


def test_key_reader_module_imports_without_posix_modules() -> None:
    """The controller must import on hosts lacking termios/tty, such as Windows.

    Blocking the POSIX modules in a subprocess proves the imports are lazy
    rather than relying on the current platform happening to provide them.
    """
    program = """
import sys

for name in ("termios", "tty", "fcntl"):
    sys.modules[name] = None

from genai_opt.optimizer_engine.experiment_controller import TerminalController
from genai_opt.experiments.simple_experiment import build_simple_experiment

print("imported")
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "imported" in result.stdout


def test_create_key_reader_selects_windows_backend(monkeypatch) -> None:
    _pretend_tty(monkeypatch, interactive=True)
    monkeypatch.setattr(sys, "platform", "win32")

    assert isinstance(create_key_reader(), WindowsKeyReader)


def test_create_key_reader_selects_posix_backend(monkeypatch) -> None:
    _pretend_tty(monkeypatch, interactive=True)
    monkeypatch.setattr(sys, "platform", "linux")

    assert isinstance(create_key_reader(), PosixKeyReader)


def test_create_key_reader_falls_back_on_unknown_platform(monkeypatch) -> None:
    _pretend_tty(monkeypatch, interactive=True)
    monkeypatch.setattr(sys, "platform", "some-future-os")

    assert isinstance(create_key_reader(), NullKeyReader)


def test_create_key_reader_falls_back_when_stdin_is_not_a_tty(monkeypatch) -> None:
    _pretend_tty(monkeypatch, interactive=False)
    monkeypatch.setattr(sys, "platform", "linux")

    reader = create_key_reader()
    assert isinstance(reader, NullKeyReader)
    assert reader.can_read_keys is False


def test_stdin_is_not_interactive_when_stdin_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", None)

    assert stdin_is_interactive() is False


def test_stdin_is_not_interactive_when_fileno_is_detached(monkeypatch) -> None:
    class _Detached:
        def isatty(self) -> bool:
            return True

        def fileno(self) -> int:
            raise ValueError("underlying buffer has been detached")

    monkeypatch.setattr(sys, "stdin", _Detached())

    assert stdin_is_interactive() is False


def test_controller_disables_pause_listening_without_a_usable_reader() -> None:
    controller = TerminalController(key_reader=NullKeyReader())

    assert controller.listen_for_pause is False


def test_setup_does_not_touch_the_reader_when_listening_is_off() -> None:
    reader = _ScriptedKeyReader([])
    controller = TerminalController(listen_for_pause=False, key_reader=reader)

    asyncio.run(controller.setup())

    assert reader.opened == 0
    assert controller.is_paused() is False


def test_pause_key_toggles_paused_state() -> None:
    reader = _ScriptedKeyReader(["p"])
    controller = TerminalController(key_reader=reader)

    async def scenario() -> tuple[bool, bool]:
        await controller.setup()
        paused = await _wait_until(controller.is_paused)
        reader.keys.append("p")
        resumed = await _wait_until(lambda: not controller.is_paused())
        await controller.teardown()
        return paused, resumed

    paused, resumed = asyncio.run(scenario())

    assert paused is True
    assert resumed is True


def test_teardown_cancels_the_listener_and_restores_the_reader() -> None:
    reader = _ScriptedKeyReader([])
    controller = TerminalController(key_reader=reader)

    async def scenario() -> asyncio.Task:
        await controller.setup()
        task = controller._listener_task
        await controller.teardown()
        return task

    task = asyncio.run(scenario())

    assert task is not None
    assert task.done()
    assert reader.opened == 1
    assert reader.closed == 1


def test_teardown_is_safe_without_setup() -> None:
    reader = _ScriptedKeyReader([])
    controller = TerminalController(key_reader=reader)

    asyncio.run(controller.teardown())

    assert reader.closed == 0


def test_unrecognized_keys_leave_the_state_alone() -> None:
    controller = TerminalController(key_reader=NullKeyReader())

    controller._handle_key("x")
    assert controller.is_paused() is False

    controller._handle_key(None)
    assert controller.is_paused() is False


def test_null_reader_sleeps_for_the_poll_interval() -> None:
    """Guards against a polling caller turning this reader into a busy loop."""
    reader = NullKeyReader(poll_interval=0.05)

    start = time.monotonic()
    assert reader.read_key() is None
    elapsed = time.monotonic() - start

    assert elapsed >= 0.04


async def _wait_until(predicate, timeout: float = 2.0) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.01)
    pytest.fail("condition was not met before the timeout")
