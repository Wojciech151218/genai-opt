import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from genai_opt.adapters.simple_system_prompt_genome import (
    SimpleSystemPromptGenome,
    SimpleSystemPromptPhenotype,
    crossover_prompt_function,
    invoke_task_message_function,
    mutate_prompt_function,
)
from genai_opt.adapters.simple_system_prompt_genome.helpers import llm_to_config
from genai_opt.experiments.float_genome import FloatGenome
from genai_opt.experiments.haiku_experiment import HaikuOutput, evaluate_haiku_function
from genai_opt.optimizer_engine.checkpointer.filesystem import FilesystemCheckpointer
from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.operation import Operation
from genai_opt.optimizer_engine.population import Population


class _StubChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "stub"

    @property
    def model_name(self) -> str:
        return "stub-model"

    @property
    def temperature(self) -> float:
        return 0.5

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError

    def with_structured_output(self, schema, **kwargs):
        return self


def _stub_evaluate():
    async def evaluate(_invocation: HaikuOutput) -> Operation[float]:
        return Operation(1.0)

    return evaluate


def test_float_genome_json_roundtrip() -> None:
    genome = FloatGenome(42.0, target=50.0, mutation_scale=2.5)
    genome._set_invocation(42.0)
    genome._set_evaluation(92.0)

    restored = FloatGenome.from_json(genome.to_json())

    assert restored.phenotype == 42.0
    assert restored.target == 50.0
    assert restored.mutation_scale == 2.5
    assert restored.invocation == 42.0
    assert restored.evaluation == 92.0


def test_simple_system_prompt_genome_json_roundtrip() -> None:
    llm = _StubChatModel()
    task = HumanMessage(content="Write a haiku.")
    restore_context = {
        "invocation_schema": HaikuOutput,
        "invoke_function": invoke_task_message_function(task, HaikuOutput),
        "evaluate_function": evaluate_haiku_function(llm),
        "mutate_function": mutate_prompt_function("Mutate: {system_prompt}", llm),
        "crossover_function": crossover_prompt_function("A: {prompt_a} B: {prompt_b}", llm),
        "llm": llm,
    }
    genome = SimpleSystemPromptGenome(
        phenotype=SimpleSystemPromptPhenotype(system_prompt="You are a poet.", llm=llm),
        invocation_schema=restore_context["invocation_schema"],
        invoke_function=restore_context["invoke_function"],
        evaluate_function=restore_context["evaluate_function"],
        mutate_function=restore_context["mutate_function"],
        crossover_function=restore_context["crossover_function"],
    )
    genome._set_invocation(
        HaikuOutput(
            line_one="one two three four five",
            line_two="one two three four five six seven",
            line_three="one two three four five",
        )
    )
    genome._set_evaluation(80.0)

    payload = genome.to_json()
    restored = SimpleSystemPromptGenome.from_json(payload, **restore_context)

    assert payload["system_prompt"] == "You are a poet."
    assert payload["llm_config"] == llm_to_config(llm)
    assert payload["invocation_schema"].endswith("HaikuOutput")
    assert restored.phenotype.system_prompt == "You are a poet."
    assert restored.evaluation == 80.0
    assert restored.invocation.line_one == "one two three four five"


def test_simple_system_prompt_genome_from_json_requires_restore_context() -> None:
    llm = _StubChatModel()
    genome = SimpleSystemPromptGenome(
        phenotype=SimpleSystemPromptPhenotype(system_prompt="Prompt", llm=llm),
        invocation_schema=HaikuOutput,
        invoke_function=invoke_task_message_function(HumanMessage(content="task"), HaikuOutput),
        evaluate_function=_stub_evaluate(),
        mutate_function=mutate_prompt_function("Mutate: {system_prompt}", llm),
        crossover_function=crossover_prompt_function("A: {prompt_a}", llm),
    )

    with pytest.raises(ValueError, match="Missing restore context"):
        SimpleSystemPromptGenome.from_json(genome.to_json())


def test_filesystem_checkpointer_json_roundtrip(tmp_path) -> None:
    population = Population(
        [
            FloatGenome(10.0, target=50.0),
            FloatGenome(20.0, target=50.0),
        ]
    )
    population.population[0]._set_invocation(10.0)
    population.population[0]._set_evaluation(90.0)
    population.population[1]._set_invocation(20.0)
    population.population[1]._set_evaluation(70.0)

    metadata = IterationMetadata.from_population(iteration=1, population=population, operations=[])
    checkpointer = FilesystemCheckpointer(tmp_path)
    checkpointer.save_checkpoint(population, 1, metadata)

    restored_population, iteration = checkpointer.load()
    assert iteration == 1
    assert restored_population.get_genome_count() == 2
    assert restored_population.population[0].phenotype == 10.0
    assert restored_population.population[0].evaluation == 90.0
    assert (tmp_path / "checkpoint.json").exists()
    assert not (tmp_path / "checkpoint.pkl").exists()
