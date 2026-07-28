"""Shared test configuration.

Puts the ``tests`` directory on the import path so helper modules such as
``fakes`` can be imported from any subdirectory.
"""

import sys
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent
if str(_TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TESTS_ROOT))
