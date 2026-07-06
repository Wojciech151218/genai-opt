from __future__ import annotations

import asyncio
import os
from random import choice

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from genai_opt.adapters.simple_system_prompt_genome import (
    SimpleSystemPromptGenome,
    SimpleSystemPromptPhenotype,
    SystemPrompt,
    crossover_prompt_function,
    evaluate_prompt_function,
    invoke_task_message_function,
    mutate_prompt_function,
    render_system_prompt,
)
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Population,
    ReproductionPolicy,
    TerminalLoggerMetricsCollector,
    cycle_seeds_initial_population,
    cycle_seeds_initial_population_strategy,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
)

DEFAULT_ITERATIONS = 5
DEFAULT_MUTATION_RATE = 0.35
DEFAULT_POPULATION_SIZE = 8
DEFAULT_MODEL = "gpt-4o-mini"

CULTURAL_THEMES = (
    "hanami (cherry blossom viewing) and mono no aware",
    "tsukimi (autumn moon viewing) and harvest gratitude",
    "matsuri (summer festival) lanterns and community",
    "yuki (first snow) and quiet winter stillness",
    "tanabata wishes and the Weaver Star",
)

SEED_SYSTEM_PROMPTS: tuple[str, ...] = (
    "You are a haiku poet. Write three-line poems with seasonal imagery.",
    (
        "You are a student of Matsuo Basho. Write haiku in English that honor "
        "mono no aware and use vivid kigo (season words)."
    ),
    (
        "You are a guide to Japanese aesthetics. Compose haiku that weave "
        "cultural tradition, nature, and wabi-sabi into spare language."
    ),
    (
        "You teach classical haiku. Each poem must have three lines in a "
        "5-7-5 syllable rhythm and reference a living cultural practice."
    ),
    (
        "You are a temple gardener and poet. Write haiku where every image "
        "carries seasonal and spiritual significance from Japanese culture."
    ),
    (
        "You preserve folk haiku traditions. Ground each poem in a specific "
        "custom, festival, or craft and let silence between lines breathe."
    ),
    (
        "You write for a cultural anthology. Haiku must feel poetic, precise, "
        "and rooted in Japanese heritage rather than generic nature verse."
    ),
    (
        "You channel the Shiki-era discipline of haiku. Use concrete sensory "
        "detail and a culturally meaningful turn in the final line."
    ),
)

MUTATE_PROMPT = """\
You evolve system prompts for a haiku-writing assistant.

Improve the prompt below so the model produces more poetic haiku with deeper \
cultural significance: stronger kigo, clearer references to Japanese customs, \
and language that feels spare yet resonant.

Current system prompt:
{system_prompt}

Return one improved system prompt. Keep it concise and actionable."""

CROSSOVER_PROMPT = """\
You combine two system prompts for a haiku-writing assistant.

Merge the best ideas from both into a single prompt that encourages poetic \
haiku with authentic cultural significance.

Prompt A:
{self}

Prompt B:
{other}

Return one unified system prompt."""

EVALUATE_PROMPT = """\
You judge haiku outputs for an evolutionary optimizer.

Score the candidate on:
- Poetic quality (imagery, rhythm, restraint)
- Syllable structure (classic 5-7-5 intent in English)
- Cultural significance (kigo, tradition, aesthetics, specific cultural context)

Candidate output (JSON):
{output}

Return a score from 0 to 100. Reserve 90+ for masterful, culturally grounded haiku."""


class HaikuOutput(BaseModel):
    line_one: str = Field(description="First line (~5 syllables)")
    line_two: str = Field(description="Second line (~7 syllables)")
    line_three: str = Field(description="Third line (~5 syllables)")
    cultural_reference: str = Field(description="The Japanese tradition, festival, aesthetic, or symbol referenced")
    significance: str = Field(description="One sentence on why the haiku carries cultural weight")


class HaikuEvaluation(BaseModel):
    score: float = Field(description="Overall fitness from 0 to 100 for poetic and cultural quality")


def create_llm(
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
) -> BaseChatModel:
    return init_chat_model(model, temperature=temperature)


def build_haiku_task_message(theme: str | None = None) -> HumanMessage:
    topic = theme or choice(CULTURAL_THEMES)
    return HumanMessage(
        content=(
            f"Write a haiku about {topic}. "
            "The poem should feel poetic, observe 5-7-5 syllable rhythm in English, "
            "and carry genuine cultural significance rather than generic nature imagery."
        )
    )


def create_haiku_genome(
    llm: BaseChatModel,
    system_prompt: SystemPrompt,
    *,
    task_message: HumanMessage | None = None,
) -> SimpleSystemPromptGenome[HaikuOutput]:
    task = task_message or build_haiku_task_message()
    phenotype = SimpleSystemPromptPhenotype(system_prompt=system_prompt, llm=llm)
    return SimpleSystemPromptGenome(
        phenotype=phenotype,
        invocation_schema=HaikuOutput,
        invoke_function=invoke_task_message_function(task, HaikuOutput),
        evaluate_function=evaluate_prompt_function(EVALUATE_PROMPT, llm, HaikuEvaluation),
        mutate_function=mutate_prompt_function(MUTATE_PROMPT, llm),
        crossover_function=crossover_prompt_function(CROSSOVER_PROMPT, llm),
    )


def create_initial_population(
    llm: BaseChatModel,
    population_size: int = DEFAULT_POPULATION_SIZE,
    *,
    shared_task: HumanMessage | None = None,
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    task_message = shared_task or build_haiku_task_message()
    return cycle_seeds_initial_population(
        SEED_SYSTEM_PROMPTS,
        lambda seed: create_haiku_genome(llm, seed, task_message=task_message),
        population_size=population_size,
    )


def build_haiku_experiment(
    llm: BaseChatModel,
    *,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    shared_task: HumanMessage | None = None,
) -> ExperimentBuilder[SimpleSystemPromptPhenotype, HaikuOutput]:
    task_message = shared_task or build_haiku_task_message()
    return ExperimentBuilder(
        inital_population_strategy=cycle_seeds_initial_population_strategy(
            SEED_SYSTEM_PROMPTS,
            lambda seed: create_haiku_genome(llm, seed, task_message=task_message),
            population_size=population_size,
        ),
        convergence_criterion=iteration_limited_convergence(iterations),
        mutation_policy=random_mutation(mutation_rate),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(population_size),
            tournament_selection,
        ),
        metrics_collector=TerminalLoggerMetricsCollector(),
    )


async def run_haiku_experiment(
    llm: BaseChatModel | None = None,
    *,
    model: str = DEFAULT_MODEL,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    shared_task: HumanMessage | None = None,
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    chat_model = llm or create_llm(model=model)
    engine = build_haiku_experiment(
        chat_model,
        iterations=iterations,
        mutation_rate=mutation_rate,
        population_size=population_size,
        shared_task=shared_task,
    ).build()
    return await engine.run()


def format_haiku(haiku: HaikuOutput) -> str:
    return (
        f"{haiku.line_one}\n{haiku.line_two}\n{haiku.line_three}\n  → {haiku.cultural_reference}: {haiku.significance}"
    )


def print_best_result(population: Population[SimpleSystemPromptPhenotype, HaikuOutput]) -> None:
    best_genome, best_fitness = max(
        population.get_genome_fitness(),
        key=lambda item: item[1],
    )
    haiku = best_genome.invocation
    print("\n=== Best evolved system prompt ===")
    print(render_system_prompt(best_genome.phenotype.system_prompt))
    print(f"\nFitness: {best_fitness:.2f}")
    print("\n=== Sample haiku ===")
    print(format_haiku(haiku))


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Set OPENAI_API_KEY before running the haiku experiment, "
            "or pass a configured chat model to run_haiku_experiment()."
        )

    population = asyncio.run(
        run_haiku_experiment(
            iterations=DEFAULT_ITERATIONS,
            population_size=DEFAULT_POPULATION_SIZE,
        )
    )
    print_best_result(population)


if __name__ == "__main__":
    main()
