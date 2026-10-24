"""The checkpointer contract and its do-nothing default."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic

from genai_opt.optimizer_engine.engine_state import EngineState
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.utils.typevars import Inv, P


class Checkpointer(ABC, Generic[P, Inv]):
    """Saves and restores engine state so a run can survive interruption.

    The engine saves after every phase, not every iteration, so an interrupted
    run resumes without repeating the phase it had already completed. For
    LLM-backed experiments that is the difference between losing a few seconds
    and paying for a whole generation again.
    """

    @abstractmethod
    def save_checkpoint(
        self,
        state: EngineState[P, Inv],
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        """Persist the state produced by the phase that just finished.

        Implementations should write atomically, since the engine may be killed
        mid-write; a half-written checkpoint is worse than none.

        Args:
            state: The state to persist, whose ``phase`` is the next one to run.
            iteration_metadata: What the finished phase produced, suitable for a
                human-readable summary alongside the state.
        """
        raise NotImplementedError("Checkpointer.save_checkpoint() is not implemented")

    @abstractmethod
    def load(self, **context: Any) -> EngineState[P, Inv] | None:
        """Restore previously saved state.

        Args:
            **context: Collaborators that genomes cannot serialize, such as a
                chat model or the evaluation function.

        Returns:
            The restored state, or ``None`` when nothing has been saved, so that
            a first run and a resumed run share one code path.
        """
        raise NotImplementedError("Checkpointer.load() is not implemented")


class NullCheckpointer(Checkpointer[P, Inv]):
    """Keeps nothing, so a run always starts fresh.

    The engine's default. Suitable for cheap experiments and tests; using it for
    an LLM-backed run means an interruption discards everything already spent.
    """

    def save_checkpoint(
        self,
        state: EngineState[P, Inv],
        iteration_metadata: IterationMetadata[P, Inv],
    ) -> None:
        """Discard the state."""

    def load(self, **context: Any) -> EngineState[P, Inv] | None:
        """Report that there is nothing to resume."""
        return None
