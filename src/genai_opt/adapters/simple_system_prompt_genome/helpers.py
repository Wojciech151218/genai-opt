from __future__ import annotations

from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel

from genai_opt.adapters.simple_system_prompt_genome.types import SystemPrompt
from genai_opt.env import load_project_env
from genai_opt.optimizer_engine.utils.timed_operation import AdapterResult, build_operation

__all__ = [
    "AdapterResult",
    "build_invoke_chat_prompt",
    "build_operation",
    "ensure_prompt_template",
    "extract_parsed",
    "extract_score",
    "format_invocation_for_evaluation",
    "llm_from_config",
    "llm_to_config",
    "render_system_prompt",
    "system_message_template",
]


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


def llm_to_config(llm: BaseChatModel) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for key in ("model", "model_name", "temperature", "model_provider", "max_tokens"):
        value = getattr(llm, key, None)
        if value is not None:
            config[key] = value
    model = config.get("model") or config.get("model_name")
    if model is not None:
        config["model"] = model
    return config


def llm_from_config(config: dict[str, Any], *, api_key: str | None = None) -> BaseChatModel:
    load_project_env()
    model = config.get("model") or config.get("model_name")
    if model is None:
        raise ValueError("LLM config must include 'model' or 'model_name'")
    kwargs = {key: config[key] for key in ("temperature", "model_provider", "max_tokens") if key in config}
    if api_key is not None:
        kwargs["api_key"] = api_key
    return init_chat_model(model, **kwargs)
