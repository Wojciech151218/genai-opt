from __future__ import annotations

from typing import Any

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel

from genai_opt.adapters.simple_system_prompt_genome.types import SystemPrompt
from genai_opt.optimizer_engine.operation import Operation


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


def extract_parsed(result: Any) -> Any:
    """Unwrap the parsed value from a ``with_structured_output(include_raw=True)`` result."""
    if isinstance(result, dict) and "parsed" in result:
        parsing_error = result.get("parsing_error")
        if parsing_error is not None:
            raise parsing_error
        return result["parsed"]
    return result


def build_operation[V](
    value: V,
    result: Any,
    *,
    time_seconds: float | None = None,
) -> Operation[V]:
    """Wrap a value in an Operation, attaching LLM metadata from the raw AIMessage.

    Applies ``Operation.from_ai_message`` when the ``include_raw=True`` result
    carries a raw message with a recognizable usage shape; falls back to a bare
    Operation otherwise.
    """
    raw_message = result.get("raw") if isinstance(result, dict) else None
    if raw_message is not None:
        try:
            return Operation.from_ai_message(value, raw_message, time_seconds=time_seconds)
        except ValueError:
            pass
    return Operation(value)
