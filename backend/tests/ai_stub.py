"""Заглушка модели LangChain: проигрывает заданные ответы и запоминает всё, что ей показали."""

import json
import time
from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from app.config import Settings

Reply = AIMessage | Exception


def call_search(**arguments: Any) -> AIMessage:  # noqa: ANN401
    """Ответ модели: вызвать инструмент поиска слотов."""
    call = {"name": "search_slots", "args": arguments, "id": f"call-{time.monotonic_ns()}"}
    return AIMessage(content="", tool_calls=[call])


def final_answer(text: str, *starts_at: str) -> AIMessage:
    """Ответ модели: итоговый структурированный ответ `{text, slots}`."""
    answer = {"text": text, "slots": [{"starts_at": value} for value in starts_at]}
    call = {"name": "AgentAnswer", "args": answer, "id": f"final-{time.monotonic_ns()}"}
    return AIMessage(content="", tool_calls=[call])


class ScriptedChatModel(BaseChatModel):
    """Отвечает по сценарию; `Exception` в сценарии — сбой модели."""

    script: list[Any]
    delay_seconds: float = 0
    requests: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(
        self,
        tools: Sequence[Any],  # noqa: ARG002
        **_: Any,  # noqa: ANN401
    ) -> "ScriptedChatModel":
        """Инструменты не нужны: ответы заданы сценарием."""
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,  # noqa: ARG002
        run_manager: CallbackManagerForLLMRun | None = None,  # noqa: ARG002
        **_: Any,  # noqa: ANN401
    ) -> ChatResult:
        self.requests.append(list(messages))
        time.sleep(self.delay_seconds)
        reply = self.script[len(self.requests) - 1]
        if isinstance(reply, Exception):
            raise reply
        return ChatResult(generations=[ChatGeneration(message=reply)])

    def tool_results(self) -> list[dict[str, Any]]:
        """Ответы инструмента, которые увидела модель (JSON), в порядке вызовов."""
        last = self.requests[-1] if self.requests else []
        results: list[dict[str, Any]] = []
        for message in last:
            if isinstance(message, ToolMessage):
                try:
                    results.append(json.loads(str(message.content)))
                except json.JSONDecodeError:
                    results.append({"error": str(message.content)})
        return results


def model_factory(model: ScriptedChatModel) -> Callable[[], Callable[[Settings], BaseChatModel]]:
    """Зависимость-фабрика, которая отдаёт заглушку вместо реальной модели."""
    return lambda: lambda _settings: model
