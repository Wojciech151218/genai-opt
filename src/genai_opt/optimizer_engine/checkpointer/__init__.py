"""Persistence of engine state so a run can be resumed after it stops.

A checkpoint is written after every phase, which matters most for LLM-backed
experiments where re-running a phase costs real money.
"""

from genai_opt.optimizer_engine.checkpointer.checkpointer import Checkpointer, NullCheckpointer
from genai_opt.optimizer_engine.checkpointer.filesystem import FilesystemCheckpointer

__all__ = ["Checkpointer", "FilesystemCheckpointer", "NullCheckpointer"]
