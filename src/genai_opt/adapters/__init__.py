"""Ready-made genomes that connect the engine to concrete GenAI tasks.

An adapter supplies the four genome operations (invoke, evaluate, mutate,
crossover) for one kind of optimization target, so an experiment only has to
describe its task rather than implement a genome from scratch.
"""

from genai_opt.adapters.simple_system_prompt_genome import (
    EvaluationScore,
    InvSchema,
    SimpleSystemPromptGenome,
    SimpleSystemPromptPhenotype,
    SystemPrompt,
    SystemPromptMutation,
    crossover_prompt_function,
    evaluate_prompt_function,
    invoke_task_message_function,
    llm_mutate_function,
    mixed_mutate_function,
    mutate_prompt_function,
    render_system_prompt,
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
