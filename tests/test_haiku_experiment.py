from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from genai_opt.experiments.haiku_experiment import (
    HaikuOutput,
    SEED_SYSTEM_PROMPTS,
    _is_valid_haiku_structure,
    build_haiku_experiment,
    build_haiku_task_message,
    create_haiku_genome,
    create_initial_population,
)


class _StubChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "stub"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError

    def with_structured_output(self, schema, **kwargs):
        return self


def test_create_initial_population_uses_seed_prompts() -> None:
    llm = _StubChatModel()
    task = HumanMessage(content="Write a haiku about autumn.")
    population = create_initial_population(
        llm,
        population_size=4,
        shared_task=task,
    )

    assert population.get_genome_count() == 4
    for index, genome in enumerate(population.population):
        assert genome.phenotype.system_prompt == SEED_SYSTEM_PROMPTS[index % len(SEED_SYSTEM_PROMPTS)]
        assert genome.phenotype.llm is llm


def test_build_haiku_experiment_wires_population_strategy() -> None:
    llm = _StubChatModel()
    builder = build_haiku_experiment(llm, iterations=2, population_size=3)
    engine = builder.build()

    assert engine.population.get_genome_count() == 3
    assert engine.convergence_criterion(engine.population, 0) is False


def test_haiku_task_message_includes_cultural_theme() -> None:
    message = build_haiku_task_message("tsukimi (autumn moon viewing)")
    assert "tsukimi" in message.content
    assert "5-7-5" in message.content


def test_create_haiku_genome_configures_functions() -> None:
    genome = create_haiku_genome(_StubChatModel(), SEED_SYSTEM_PROMPTS[0])
    assert callable(genome._mutate_function)
    assert callable(genome._crossover_function)
    assert callable(genome._evaluate_function)
    assert callable(genome._invoke_function)


def test_is_valid_haiku_structure_checks_word_counts() -> None:
    valid = HaikuOutput(
        line_one="one two three four five",
        line_two="one two three four five six seven",
        line_three="one two three four five",
    )
    invalid = HaikuOutput(
        line_one="too few words",
        line_two="one two three four five six seven",
        line_three="one two three four five",
    )

    assert _is_valid_haiku_structure(valid) is True
    assert _is_valid_haiku_structure(invalid) is False
