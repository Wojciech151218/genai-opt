from __future__ import annotations

import asyncio
import re
import uuid
from collections.abc import Awaitable, Callable
from random import choice

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from genai_opt.adapters.simple_system_prompt_genome import (
    SimpleSystemPromptGenome,
    SimpleSystemPromptPhenotype,
    SystemPrompt,
    crossover_prompt_function,
    invoke_task_message_function,
    mutate_prompt_function,
    render_system_prompt,
)
from genai_opt.adapters.simple_system_prompt_genome.helpers import AdapterResult, extract_parsed
from genai_opt.env import load_openai_api_key
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    Population,
    ReproductionPolicy,
    SqliteCheckpointer,
    WebSocketExperimentController,
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
CHECKPOINT_DB = ".checkpoints/haiku_experiment.db"

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
{prompt_a}

Prompt B:
{prompt_b}

Return one unified system prompt."""

EVALUATE_PROMPT = """\
You are a haiku judge.

Score the candidate on:
- Poetic quality (imagery, rhythm, restraint)
- Cultural significance (kigo, tradition, aesthetics, specific cultural context)
"""


class HaikuOutput(BaseModel):
    line_one: str = Field(description="First line (~5 syllables)")
    line_two: str = Field(description="Second line (~7 syllables)")
    line_three: str = Field(description="Third line (~5 syllables)")


class HaikuEvaluation(BaseModel):
    cultural_reference: list[str] = Field(
        description="List of the Japanese tradition, festival, aesthetic, or symbol referenced"
    )
    significance: int = Field(
        description="Your judgement of the cultural significance of the haiku from 0 to 100",
        ge=0,
        le=100,
    )


_VOWEL_GROUPS = re.compile(r"[aeiouy]+", re.IGNORECASE)
_NON_LETTER = re.compile(r"[^a-z']")


def _count_word_syllables(word: str) -> int:
    word = _NON_LETTER.sub("", word.lower())
    if not word:
        return 0

    count = len(_VOWEL_GROUPS.findall(word))
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _count_line_syllables(line: str) -> int:
    return sum(_count_word_syllables(word) for word in line.split())


def _is_valid_haiku_structure(invocation: HaikuOutput) -> bool:
    return (
        _count_line_syllables(invocation.line_one) == 5
        and _count_line_syllables(invocation.line_two) == 7
        and _count_line_syllables(invocation.line_three) == 5
    )


def evaluate_haiku_function(
    llm: BaseChatModel,
) -> Callable[[HaikuOutput], Awaitable[float | AdapterResult[float]]]:
    async def evaluate(invocation: HaikuOutput) -> float | AdapterResult[float]:
        if not _is_valid_haiku_structure(invocation):
            return 0.0

        haiku = f"{invocation.line_one}\n{invocation.line_two}\n{invocation.line_three}"
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", EVALUATE_PROMPT),
                ("human", "{haiku}"),
            ]
        )
        structured_llm = llm.with_structured_output(HaikuEvaluation, include_raw=True)
        result = await (prompt_template | structured_llm).ainvoke({"haiku": haiku})
        evaluation = extract_parsed(result)
        score = float(len(evaluation.cultural_reference) * evaluation.significance)
        return AdapterResult(score, raw=result)

    return evaluate


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
        evaluate_function=evaluate_haiku_function(llm),
        mutate_function=mutate_prompt_function(MUTATE_PROMPT, llm),
        crossover_function=crossover_prompt_function(CROSSOVER_PROMPT, llm),
    )


def create_initial_population(
    llm: BaseChatModel,
    population_size: int = DEFAULT_POPULATION_SIZE,
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    return cycle_seeds_initial_population(
        SEED_SYSTEM_PROMPTS,
        lambda seed: create_haiku_genome(llm, seed, task_message=build_haiku_task_message()),
        population_size=population_size,
    )


async def run_haiku_experiment(
    llm: BaseChatModel | None = None,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    checkpoint_db: str =  CHECKPOINT_DB,
    experiment_id: str | None = None,
    websocket_host: str = "localhost",
    websocket_port: int = 8765,
    launch_ui: bool = False,
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    chat_model = llm or init_chat_model(
        model,
        temperature=0.8,
        api_key=load_openai_api_key(api_key=api_key),
    )
    task_message = build_haiku_task_message()
    resolved_experiment_id = experiment_id or str(uuid.uuid4())
    restore_genome = create_haiku_genome(
        chat_model,
        SEED_SYSTEM_PROMPTS[0],
        task_message=task_message,
    )

    builder = ExperimentBuilder(
        inital_population_strategy=cycle_seeds_initial_population_strategy(
            SEED_SYSTEM_PROMPTS,
            lambda seed: create_haiku_genome(chat_model, seed, task_message=task_message),
            population_size=population_size,
        ),
        convergence_criterion=iteration_limited_convergence(iterations),
        mutation_policy=random_mutation(mutation_rate),
        reproduction_policy=ReproductionPolicy(
            generational_reproduction(population_size),
            tournament_selection,
        ),
        checkpointer=SqliteCheckpointer(
            db_path=checkpoint_db,
            experiment_id=resolved_experiment_id,
            genome=restore_genome,
        ),
        experiment_controller=WebSocketExperimentController(host=websocket_host, port=websocket_port),
    )
    if launch_ui:
        builder.start_dashboard()

    engine = builder.build().from_checkpoint()
    return await engine.run()


def format_haiku(haiku: HaikuOutput) -> str:
    return f"{haiku.line_one}\n{haiku.line_two}\n{haiku.line_three}"


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
    population = asyncio.run(
        run_haiku_experiment(
            iterations=DEFAULT_ITERATIONS,
            population_size=DEFAULT_POPULATION_SIZE,
            launch_ui=True,
        )
    )
    print_best_result(population)


if __name__ == "__main__":
    main()
