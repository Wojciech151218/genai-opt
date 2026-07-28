"""Small building blocks shared by the system-prompt adapter's functions.

Chiefly they smooth over the fact that a system prompt may be plain text or a
``PromptTemplate``, and that a chat model must be reduced to a serializable
description to survive checkpointing.
"""

from __future__ import annotations

from typing import Any, TypeVar

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
from genai_opt.optimizer_engine.operation import Operation

V = TypeVar("V")


def render_system_prompt(prompt: SystemPrompt) -> str:
    """Render a system prompt to the text a human should read.

    Templates are formatted with no arguments, so this only suits prompts whose
    placeholders are already filled in. Used for display and for checkpointing.

    Raises:
        KeyError: If the template still has unfilled placeholders.
    """
    if isinstance(prompt, str):
        return prompt
    return prompt.format()


def ensure_prompt_template(prompt: SystemPrompt) -> PromptTemplate:
    """Return ``prompt`` as a template, wrapping plain text if needed."""
    if isinstance(prompt, str):
        return PromptTemplate.from_template(prompt)
    return prompt


def system_message_template(
    system_prompt: SystemPrompt,
) -> tuple[str, str] | SystemMessagePromptTemplate:
    """Convert a system prompt into a system message for a chat prompt.

    Plain text becomes a ``("system", text)`` pair so LangChain does not treat
    stray braces as placeholders; templates keep their placeholders.
    """
    if isinstance(system_prompt, str):
        return ("system", system_prompt)
    return SystemMessagePromptTemplate(prompt=system_prompt)


def build_invoke_chat_prompt(system_prompt: SystemPrompt) -> ChatPromptTemplate:
    """Build the chat prompt used to invoke a genome.

    The result takes a ``task_messages`` variable, which is how the same evolving
    system prompt is paired with a fixed task for every genome in a population.
    """
    return ChatPromptTemplate.from_messages(
        [
            system_message_template(system_prompt),
            MessagesPlaceholder("task_messages"),
        ]
    )


def format_invocation_for_evaluation(invocation: BaseModel) -> str:
    """Render an invocation as JSON for the judging model to read."""
    return invocation.model_dump_json()


def extract_score(result: BaseModel) -> float:
    """Read the fitness out of a parsed evaluation reply.

    Args:
        result: The judging model's parsed reply.

    Returns:
        The score as a float.

    Raises:
        ValueError: If the evaluation schema defines no ``score`` field.
    """
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


def build_operation(
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


def llm_to_config(llm: BaseChatModel) -> dict[str, Any]:
    """Reduce a chat model to a checkpoint-safe description of itself.

    Only the model name and a few generation settings are kept. Credentials are
    deliberately excluded, so a checkpoint never carries an API key; supply the
    key again through the restore context or the environment.
    """
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
    """Rebuild a chat model from a description produced by :func:`llm_to_config`.

    Args:
        config: The stored description.
        api_key: Key to use. When omitted the provider's usual environment
            variable is used, after loading the project ``.env``.

    Returns:
        The reconstructed chat model.

    Raises:
        ValueError: If the description names no model.
    """
    load_project_env()
    model = config.get("model") or config.get("model_name")
    if model is None:
        raise ValueError("LLM config must include 'model' or 'model_name'")
    kwargs = {key: config[key] for key in ("temperature", "model_provider", "max_tokens") if key in config}
    if api_key is not None:
        kwargs["api_key"] = api_key
    return init_chat_model(model, **kwargs)
