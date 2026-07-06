from __future__ import annotations

from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

SystemPrompt = str | PromptTemplate
InvSchema = TypeVar("InvSchema", bound=BaseModel)


class EvaluationScore(BaseModel):
    score: float = Field(description="Fitness score for the invocation output")


class SystemPromptMutation(BaseModel):
    system_prompt: str = Field(description="The evolved system prompt")


class SimpleSystemPromptPhenotype(BaseModel):
    system_prompt: SystemPrompt = Field(description="The system prompt")
    llm: BaseChatModel = Field(description="The LLM to use for the system prompt")
