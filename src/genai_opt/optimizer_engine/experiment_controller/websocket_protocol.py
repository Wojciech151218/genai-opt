from typing import Literal

from pydantic import BaseModel


class ClientCommandMessage(BaseModel):
    """Message sent by the client to control the engine."""

    command: Literal["pause", "resume"]


class ServerStatusMessage(BaseModel):
    """Message broadcasted by the server when the engine state changes."""

    type: Literal["status"] = "status"
    status: Literal["running", "paused", "stopped"]


class ServerIterationMessage(BaseModel):
    """Message broadcasted by the server when a new iteration phase begins."""

    type: Literal["iteration"] = "iteration"
    iteration: int
    phase: str
    population_size: int = 0


class ServerOperationMessage(BaseModel):
    """Message broadcasted by the server when an operation starts or finishes."""

    type: Literal["operation"] = "operation"
    iteration: int
    phase: str
    operation_kind: str
    duration: float | None = None
