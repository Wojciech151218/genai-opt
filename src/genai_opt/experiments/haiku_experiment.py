"""An LLM-backed experiment that evolves a haiku-writing system prompt.

Unlike :mod:`~genai_opt.experiments.simple_experiment`, running this costs money:
every genome is invoked and judged by a real model each iteration, and mutation
and crossover are model calls too. With the defaults, one iteration is roughly
``population_size`` invocations plus the same number of evaluations, plus a
mutation per selected offspring and a crossover per child.

To try it without spending anything, build the experiment with a stub chat model
via :func:`build_haiku_experiment` rather than calling
:func:`run_haiku_experiment`; the tests do exactly that. Credentials come from
``OPENAI_API_KEY`` in the environment or the project ``.env``, and are never
written to checkpoints.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
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
from genai_opt.adapters.simple_system_prompt_genome.helpers import build_operation, extract_parsed
from genai_opt.env import load_project_env
from genai_opt.optimizer_engine import (
    ExperimentBuilder,
    FilesystemCheckpointer,
    Population,
    ReproductionPolicy,
    TerminalController,
    cycle_seeds_initial_population,
    cycle_seeds_initial_population_strategy,
    generational_reproduction,
    iteration_limited_convergence,
    random_mutation,
    tournament_selection,
)
from genai_opt.optimizer_engine.operation import Operation

DEFAULT_ITERATIONS = 5
DEFAULT_MUTATION_RATE = 0.35
DEFAULT_POPULATION_SIZE = 8
DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

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
    """The invocation schema: a haiku as three separate lines.

    Splitting the lines apart lets the syllable check inspect each one, which a
    single free-text field would not allow.
    """

    line_one: str = Field(description="First line (~5 syllables)")
    line_two: str = Field(description="Second line (~7 syllables)")
    line_three: str = Field(description="Third line (~5 syllables)")


class HaikuEvaluation(BaseModel):
    """The judging schema: which traditions a haiku draws on, and how strongly.

    Fitness multiplies the two, so a poem is rewarded both for referencing
    several traditions and for doing so meaningfully.
    """

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
) -> Callable[[HaikuOutput], Awaitable[Operation[float]]]:
    """Build the two-stage haiku evaluation used by this experiment.

    Form is checked in code first: anything that is not 5-7-5 scores zero and no
    model is called, which keeps the judging budget for poems worth judging. The
    rest are scored by the model as the number of traditions referenced times
    their significance.

    Args:
        llm: Model acting as the judge.

    Returns:
        An async evaluation function for the genome.
    """

    async def evaluate(invocation: HaikuOutput) -> Operation[float]:
        if not _is_valid_haiku_structure(invocation):
            return Operation(0.0)

        haiku = f"{invocation.line_one}\n{invocation.line_two}\n{invocation.line_three}"
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", EVALUATE_PROMPT),
                ("human", "{haiku}"),
            ]
        )
        structured_llm = llm.with_structured_output(HaikuEvaluation, include_raw=True)
        start = time.perf_counter()
        result = await (prompt_template | structured_llm).ainvoke({"haiku": haiku})
        elapsed = time.perf_counter() - start
        evaluation = extract_parsed(result)
        score = float(len(evaluation.cultural_reference) * evaluation.significance)
        return build_operation(score, result, time_seconds=elapsed)

    return evaluate


def create_llm(
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    *,
    api_key: str | None = None,
) -> BaseChatModel:
    """Create the chat model this experiment runs on.

    Args:
        model: Model identifier.
        temperature: Sampling temperature. The default is deliberately high,
            since near-identical poems give the search nothing to select between.
        api_key: Key to use. Falls back to ``OPENAI_API_KEY`` from the
            environment or the project ``.env``.

    Returns:
        The configured chat model.

    Raises:
        RuntimeError: If no key is available, rather than failing later mid-run
            with a provider error.
    """
    load_project_env()
    resolved_api_key = api_key or os.getenv(OPENAI_API_KEY_ENV)
    if not resolved_api_key:
        raise RuntimeError(
            f"Set {OPENAI_API_KEY_ENV} or pass api_key to create_llm(), "
            "or pass a configured chat model to run_haiku_experiment()."
        )
    return init_chat_model(model, temperature=temperature, api_key=resolved_api_key)


def build_haiku_task_message(theme: str | None = None) -> HumanMessage:
    """Build the task every genome in a population is asked to perform.

    Args:
        theme: Cultural theme to write about. A random one from
            ``CULTURAL_THEMES`` is chosen when omitted.

    Returns:
        The task message. Share one across a population so that the system prompt
        is the only thing being compared.
    """
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
    """Build one genome around a starting system prompt.

    Args:
        llm: Model used for writing, judging, mutating and crossing over.
        system_prompt: The prompt this genome starts from.
        task_message: Task to perform. A random themed one is built when omitted.

    Returns:
        The configured genome.
    """
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


def haiku_checkpoint_restore_context(
    llm: BaseChatModel,
    task_message: HumanMessage,
) -> dict[str, object]:
    """Build the restore context a checkpointed haiku genome needs.

    Checkpoints hold prompt text but not the closures that operate on it, so
    resuming requires handing those functions back. Pass the same task message
    used originally, or the resumed run measures something different.

    Args:
        llm: Model to rebind the operation functions to.
        task_message: The task the population was invoked with.

    Returns:
        A context mapping suitable for
        :class:`~genai_opt.optimizer_engine.checkpointer.FilesystemCheckpointer`.
    """
    return {
        "invocation_schema": HaikuOutput,
        "invoke_function": invoke_task_message_function(task_message, HaikuOutput),
        "evaluate_function": evaluate_haiku_function(llm),
        "mutate_function": mutate_prompt_function(MUTATE_PROMPT, llm),
        "crossover_function": crossover_prompt_function(CROSSOVER_PROMPT, llm),
        "llm": llm,
    }


def create_initial_population(
    llm: BaseChatModel,
    population_size: int = DEFAULT_POPULATION_SIZE,
    *,
    shared_task: HumanMessage | None = None,
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    """Build generation zero from the seed system prompts.

    Args:
        llm: Model every genome uses.
        population_size: Genomes to create. Seeds repeat when this exceeds their
            number.
        shared_task: Task all genomes perform. A random themed one is built when
            omitted.

    Returns:
        The starting population.
    """
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
    checkpoint_dir: str | Path | None = None,
) -> ExperimentBuilder[SimpleSystemPromptPhenotype, HaikuOutput]:
    """Assemble the experiment without running it.

    This is the entry point to use with a stub or recorded chat model, since it
    takes the model as an argument and calls nothing itself.

    Args:
        llm: Model used for writing, judging, mutating and crossing over.
        iterations: How many iterations to run before stopping. This is the main
            control on total spend.
        mutation_rate: Probability that a given offspring is mutated, each
            mutation being one model call.
        population_size: Genomes per generation.
        shared_task: Task all genomes perform. A random themed one is built when
            omitted.
        checkpoint_dir: Where to write checkpoints, with the restore context
            already wired up. ``None`` keeps nothing.

    Returns:
        The configured builder.
    """
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
        checkpointer=FilesystemCheckpointer(
            checkpoint_dir,
            restore_context=haiku_checkpoint_restore_context(llm, task_message),
        )
        if checkpoint_dir
        else None,
        experiment_controller=TerminalController(),
    )


def run_haiku_experiment(
    llm: BaseChatModel | None = None,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    mutation_rate: float = DEFAULT_MUTATION_RATE,
    population_size: int = DEFAULT_POPULATION_SIZE,
    shared_task: HumanMessage | None = None,
    checkpoint_dir: str | Path | None = ".checkpoints/haiku_experiment",
) -> Population[SimpleSystemPromptPhenotype, HaikuOutput]:
    """Run the experiment to completion against a real model.

    This spends money. Resumes from ``checkpoint_dir`` when a checkpoint is there,
    which is the point: an interrupted run continues instead of paying twice.

    Args:
        llm: Model to use. Built from ``model`` and ``api_key`` when omitted.
        model: Model identifier, used only when ``llm`` is omitted.
        api_key: Key to use, falling back to the environment or project ``.env``.
        iterations: How many iterations to run before stopping.
        mutation_rate: Probability that a given offspring is mutated.
        population_size: Genomes per generation.
        shared_task: Task all genomes perform.
        checkpoint_dir: Where to read and write checkpoints. ``None`` disables
            them, so an interruption loses the run.

    Returns:
        The final population, with every genome evaluated.

    Raises:
        RuntimeError: If no model is given and no API key can be found.
    """
    chat_model = llm or create_llm(model=model, api_key=api_key)
    engine = (
        build_haiku_experiment(
            chat_model,
            iterations=iterations,
            mutation_rate=mutation_rate,
            population_size=population_size,
            shared_task=shared_task,
            checkpoint_dir=checkpoint_dir,
        )
        .build()
        .from_checkpoint()
    )
    return engine.run()


def format_haiku(haiku: HaikuOutput) -> str:
    """Join a haiku's three lines into displayable text."""
    return f"{haiku.line_one}\n{haiku.line_two}\n{haiku.line_three}"


def print_best_result(population: Population[SimpleSystemPromptPhenotype, HaikuOutput]) -> None:
    """Print the fittest genome's evolved prompt, its fitness and a sample haiku.

    Args:
        population: A finished population.

    Raises:
        ValueError: If any genome has not been evaluated or invoked.
    """
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
    """Run the experiment with default settings and print the winner.

    Calls a real model, so this spends money.
    """
    population = run_haiku_experiment(
        iterations=DEFAULT_ITERATIONS,
        population_size=DEFAULT_POPULATION_SIZE,
    )
    print_best_result(population)


if __name__ == "__main__":
    main()
