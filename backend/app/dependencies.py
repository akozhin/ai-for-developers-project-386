"""Зависимости FastAPI, которые подменяются в тестах: «сейчас» и настройки."""

from datetime import UTC, datetime
from functools import lru_cache

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Настройки приложения (читаются один раз; `create_app` перечитывает при сборке)."""
    return Settings()


def get_now() -> datetime:
    """Текущий момент (UTC); в тестах подменяется фиксированным."""
    return datetime.now(tz=UTC)
