"""Зависимости FastAPI, которые подменяются в тестах: «сейчас» и настройки."""

from collections.abc import Callable
from datetime import UTC, datetime
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Настройки приложения (читаются один раз; `create_app` перечитывает при сборке)."""
    return Settings()


def get_now() -> datetime:
    """Текущий момент (UTC); в тестах подменяется фиксированным."""
    return datetime.now(tz=UTC)


def build_chat_model(settings: Settings) -> BaseChatModel:
    """Модель AI-провайдера (OpenAI-совместимый API) из настроек."""
    return ChatOpenAI(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key or SecretStr(""),
        model=settings.ai_model,
        max_retries=0,
    )


def get_chat_model_factory() -> Callable[[Settings], BaseChatModel]:
    """Фабрика модели агента; в тестах подменяется заглушкой LangChain."""
    return build_chat_model
