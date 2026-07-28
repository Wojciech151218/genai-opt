"""An adapter that evolves the system prompt of a chat model.

The phenotype is a system prompt paired with the model that runs it. Invoking a
genome sends a fixed task message under that prompt and parses the reply into a
schema you choose; mutation and crossover ask an LLM to rewrite prompts. Compose
an experiment from the ``*_function`` factories here rather than subclassing
:class:`SimpleSystemPromptGenome`.
"""

from genai_opt.adapters.simple_system_prompt_genome.functions import (
    crossover_prompt_function,
    evaluate_prompt_function,
    invoke_task_message_function,
    llm_mutate_function,
    mixed_mutate_function,
    mutate_prompt_function,
)
from genai_opt.adapters.simple_system_prompt_genome.genome import SimpleSystemPromptGenome
from genai_opt.adapters.simple_system_prompt_genome.helpers import render_system_prompt
from genai_opt.adapters.simple_system_prompt_genome.types import (
    EvaluationScore,
    InvSchema,
    SimpleSystemPromptPhenotype,
    SystemPrompt,
    SystemPromptMutation,
)

__all__ = [
    "EvaluationScore",
    "InvSchema",
    "SimpleSystemPromptGenome",
    "SimpleSystemPromptPhenotype",
    "SystemPrompt",
    "SystemPromptMutation",
    "crossover_prompt_function",
    "evaluate_prompt_function",
    "invoke_task_message_function",
    "llm_mutate_function",
    "mixed_mutate_function",
    "mutate_prompt_function",
    "render_system_prompt",
]
