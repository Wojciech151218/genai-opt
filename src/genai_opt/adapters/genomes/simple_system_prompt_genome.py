from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Self, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel, Field

from genai_opt.optimizer_engine.genome import Genome

SystemPrompt = PromptTemplate | str
InvSchema = TypeVar("InvSchema", bound=BaseModel)


class EvaluationScore(BaseModel):
    score: float = Field(description="Fitness score for the invocation output")


class SystemPromptMutation(BaseModel):
    system_prompt: str = Field(description="The evolved system prompt")


def _render_system_prompt(prompt: SystemPrompt) -> str:
    if isinstance(prompt, str):
        return prompt
    return prompt.format()


def _ensure_prompt_template(prompt: SystemPrompt) -> PromptTemplate:
    if isinstance(prompt, str):
        return PromptTemplate.from_template(prompt)
    return prompt


def _system_message_template(system_prompt: SystemPrompt) -> tuple[str, str] | SystemMessagePromptTemplate:
    if isinstance(system_prompt, str):
        return ("system", system_prompt)
    return SystemMessagePromptTemplate(prompt=system_prompt)


def _build_system_chat_prompt(system_prompt: SystemPrompt) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([_system_message_template(system_prompt)])


def _build_invoke_chat_prompt(system_prompt: SystemPrompt) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            _system_message_template(system_prompt),
            MessagesPlaceholder("task_messages"),
        ]
    )


def _require_prompt_or_function(
    prompt: SystemPrompt | None,
    function: Callable[..., object] | None,
    operation: str,
) -> None:
    if prompt is None and function is None:
        raise ValueError(f"{operation} requires either a prompt or a function")


def _format_invocation_for_evaluation(invocation: BaseModel) -> str:
    return invocation.model_dump_json()


class SimpleSystemPromptGenome(Genome[SystemPrompt, InvSchema], Generic[InvSchema]):
    def __init__(
        self,
        llm: BaseChatModel,
        system_prompt: SystemPrompt,
        *,
        invocation_schema: type[InvSchema],
        evaluation_schema: type[BaseModel] = EvaluationScore,
        task_message: BaseMessage | None = None,
        task_function: Callable[[SystemPrompt], InvSchema] | None = None,
        mutate_prompt: SystemPrompt | None = None,
        crossover_prompt: SystemPrompt | None = None,
        mutate_function: Callable[[SystemPrompt], Self] | None = None,
        crossover_function: Callable[[SystemPrompt, SystemPrompt], Self] | None = None,
        evaluate_function: Callable[[InvSchema], float] | None = None,
        evaluate_prompt: SystemPrompt | None = None,
    ):
        super().__init__(phenotype=system_prompt)
        self._llm = llm
        self._invocation_schema = invocation_schema
        self._evaluation_schema = evaluation_schema
        self.task_message = task_message
        self.task_function = task_function
        self.mutate_prompt = mutate_prompt
        self.crossover_prompt = crossover_prompt
        self.mutate_function = mutate_function
        self.crossover_function = crossover_function
        self.evaluate_function = evaluate_function
        self.evaluate_prompt = evaluate_prompt

        self._invocation_llm = llm.with_structured_output(invocation_schema)
        self._evaluation_llm = llm.with_structured_output(evaluation_schema)
        self._mutation_llm = llm.with_structured_output(SystemPromptMutation)

    def _child(self, system_prompt: SystemPrompt) -> Self:
        return self.__class__(
            llm=self._llm,
            system_prompt=system_prompt,
            invocation_schema=self._invocation_schema,
            evaluation_schema=self._evaluation_schema,
            task_message=self.task_message,
            task_function=self.task_function,
            mutate_prompt=self.mutate_prompt,
            crossover_prompt=self.crossover_prompt,
            mutate_function=self.mutate_function,
            crossover_function=self.crossover_function,
            evaluate_function=self.evaluate_function,
            evaluate_prompt=self.evaluate_prompt,
        )

    def _extract_score(self, result: BaseModel) -> float:
        score = getattr(result, "score", None)
        if score is None:
            raise ValueError("evaluation_schema must define a 'score' field of type float")
        return float(score)

    async def invoke(self) -> InvSchema:
        _require_prompt_or_function(self.task_message, self.task_function, "invoke")
        if self.task_function is not None:
            return self.task_function(self.phenotype)

        prompt = _build_invoke_chat_prompt(self.phenotype)
        chain = prompt | self._invocation_llm
        return await chain.ainvoke({"task_messages": [self.task_message]})

    async def evaluate(self) -> float:
        _require_prompt_or_function(self.evaluate_prompt, self.evaluate_function, "evaluate")
        if self.evaluate_function is not None:
            return self.evaluate_function(self.invocation)

        prompt = _ensure_prompt_template(self.evaluate_prompt)
        chain = prompt | self._evaluation_llm
        result = await chain.ainvoke(
            {"output": _format_invocation_for_evaluation(self.invocation)}
        )
        return self._extract_score(result)

    async def mutate(self) -> Self:
        _require_prompt_or_function(self.mutate_prompt, self.mutate_function, "mutate")
        if self.mutate_function is not None:
            return self.mutate_function(self.phenotype)

        prompt = _ensure_prompt_template(self.mutate_prompt)
        chain = prompt | self._mutation_llm
        result = await chain.ainvoke({"system_prompt": _render_system_prompt(self.phenotype)})
        return self._child(result.system_prompt)

    async def crossover(self, other: Self) -> Self:
        _require_prompt_or_function(
            self.crossover_prompt, self.crossover_function, "crossover"
        )
        if self.crossover_function is not None:
            return self.crossover_function(self.phenotype, other.phenotype)

        prompt = _ensure_prompt_template(self.crossover_prompt)
        chain = prompt | self._mutation_llm
        result = await chain.ainvoke(
            {
                "self": _render_system_prompt(self.phenotype),
                "other": _render_system_prompt(other.phenotype),
            }
        )
        return self._child(result.system_prompt)
