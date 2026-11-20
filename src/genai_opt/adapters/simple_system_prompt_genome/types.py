"""Types describing what a system-prompt genome holds and produces."""

from __future__ import annotations

from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

SystemPrompt = str | PromptTemplate
"""A system prompt, either literal text or a template with placeholders."""

InvSchema = TypeVar("InvSchema", bound=BaseModel)
"""The pydantic model an invocation is parsed into."""


class EvaluationScore(BaseModel):
    """The default evaluation schema: a single fitness score.

    Any schema with a float ``score`` field works in its place, which is how an
    experiment can ask the judging model for reasoning alongside the number.
    """

    score: float = Field(description="Fitness score for the invocation output")


class SystemPromptMutation(BaseModel):
    """The reply schema used when an LLM rewrites a system prompt.

    Shared by mutation and crossover, since both produce one new prompt.
    """

    system_prompt: str = Field(description="The evolved system prompt")


class SimpleSystemPromptPhenotype(BaseModel):
    """What is being optimized: a system prompt together with the model running it.

    Bundling the model in means a population can mix models, and mutation can
    evolve the choice of model as well as the prompt text.

    Attributes:
        system_prompt: The prompt under optimization.
        llm: The chat model that runs it.
    """

    system_prompt: SystemPrompt = Field(description="The system prompt")
    llm: BaseChatModel = Field(description="The LLM to use for the system prompt")
