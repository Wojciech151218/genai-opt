"""Reading single keypresses on whatever platform the run happens to be on."""

from __future__ import annotations

import sys
import time
from abc import ABC, abstractmethod

DEFAULT_POLL_INTERVAL = 0.05


class KeyReader(ABC):
    """Reads single keypresses from a terminal without waiting for Enter.

    Backends are platform specific, so they import their platform modules
    lazily. Importing this module therefore never fails, whatever the host.

    ``read_key`` blocks for at most ``poll_interval`` seconds, which makes it
    safe to call from an executor thread inside an asyncio loop.
    """

    def __init__(self, poll_interval: float = DEFAULT_POLL_INTERVAL) -> None:
        self.poll_interval = poll_interval

    @property
    def can_read_keys(self) -> bool:
        """Whether this reader can actually deliver keypresses.

        Lets callers skip starting a listener that could never report anything.
        """
        return True

    def open(self) -> None:
        """Put the terminal into whatever mode single-key reads require."""
        return None

    def close(self) -> None:
        """Restore any terminal state changed by :meth:`open`."""
        return None

    @abstractmethod
    def read_key(self) -> str | None:
        """Return one pressed key, or ``None`` if none arrived in time."""


class NullKeyReader(KeyReader):
    """Reader for hosts with no usable interactive terminal.

    Used when stdin is not a TTY (CI logs, piped input, notebooks) or when no
    platform backend is available. It always reports "no key pressed", so
    callers need no separate non-interactive code path.
    """

    @property
    def can_read_keys(self) -> bool:
        """Always ``False``: this backend can never report a keypress."""
        return False

    def read_key(self) -> str | None:
        """Return ``None`` after sleeping for the poll interval.

        The sleep is what stops a caller that polls anyway from turning this
        into a busy loop.
        """
        time.sleep(self.poll_interval)
        return None


class PosixKeyReader(KeyReader):
    """Reader backed by ``termios``/``tty``/``select`` on Unix-like hosts.

    Cbreak mode is entered once in :meth:`open` and restored in :meth:`close`,
    rather than toggled around every poll.
    """

    def __init__(self, poll_interval: float = DEFAULT_POLL_INTERVAL) -> None:
        super().__init__(poll_interval)
        self._fd: int | None = None
        self._original_mode: list | None = None

    def open(self) -> None:
        """Enter cbreak mode, remembering the previous terminal settings."""
        import termios
        import tty

        self._fd = sys.stdin.fileno()
        self._original_mode = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)

    def read_key(self) -> str | None:
        """Wait up to the poll interval for one character on stdin."""
        import select

        ready, _, _ = select.select([sys.stdin], [], [], self.poll_interval)
        if not ready:
            return None
        return sys.stdin.read(1)

    def close(self) -> None:
        """Restore the terminal settings captured by :meth:`open`."""
        if self._fd is None or self._original_mode is None:
            return

        import termios

        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._original_mode)
        self._fd = None
        self._original_mode = None


class WindowsKeyReader(KeyReader):
    """Reader backed by ``msvcrt`` on Windows.

    Windows consoles already deliver unbuffered keypresses, so no terminal mode
    change is needed. ``msvcrt`` has no timed wait, so the poll interval is
    spent sleeping in short slices.
    """

    _SLICE_SECONDS = 0.01

    def read_key(self) -> str | None:
        """Poll the console for up to the poll interval and return any keypress."""
        import msvcrt

        deadline = time.monotonic() + self.poll_interval
        while True:
            if msvcrt.kbhit():
                return msvcrt.getwch()
            if time.monotonic() >= deadline:
                return None
            time.sleep(min(self._SLICE_SECONDS, self.poll_interval))


def stdin_is_interactive() -> bool:
    """Report whether stdin is a terminal that can deliver keypresses."""
    stdin = getattr(sys, "stdin", None)
    if stdin is None:
        return False
    try:
        return bool(stdin.isatty()) and stdin.fileno() >= 0
    except (OSError, ValueError, AttributeError):
        return False


def create_key_reader(poll_interval: float = DEFAULT_POLL_INTERVAL) -> KeyReader:
    """Return the best key reader for this host.

    Falls back to :class:`NullKeyReader` when stdin is not interactive or the
    platform has no supported backend, so callers always get a usable reader.
    """
    if not stdin_is_interactive():
        return NullKeyReader(poll_interval)
    if sys.platform == "win32":
        return WindowsKeyReader(poll_interval)
    if sys.platform.startswith(("linux", "darwin", "freebsd", "openbsd", "netbsd", "aix", "sunos", "cygwin")):
        return PosixKeyReader(poll_interval)
    return NullKeyReader(poll_interval)
