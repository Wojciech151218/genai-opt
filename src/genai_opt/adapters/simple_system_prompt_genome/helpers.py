from __future__ import annotations

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel

from genai_opt.adapters.simple_system_prompt_genome.types import SystemPrompt


def render_system_prompt(prompt: SystemPrompt) -> str:
    if isinstance(prompt, str):
        return prompt
    return prompt.format()


def ensure_prompt_template(prompt: SystemPrompt) -> PromptTemplate:
    if isinstance(prompt, str):
        return PromptTemplate.from_template(prompt)
    return prompt


def system_message_template(
    system_prompt: SystemPrompt,
) -> tuple[str, str] | SystemMessagePromptTemplate:
    if isinstance(system_prompt, str):
        return ("system", system_prompt)
    return SystemMessagePromptTemplate(prompt=system_prompt)


def build_invoke_chat_prompt(system_prompt: SystemPrompt) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            system_message_template(system_prompt),
            MessagesPlaceholder("task_messages"),
        ]
    )


def format_invocation_for_evaluation(invocation: BaseModel) -> str:
    return invocation.model_dump_json()


def extract_score(result: BaseModel) -> float:
    score = getattr(result, "score", None)
    if score is None:
        raise ValueError("evaluation_schema must define a 'score' field of type float")
    return float(score)
