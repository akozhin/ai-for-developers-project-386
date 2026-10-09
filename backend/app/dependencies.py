"""Зависимости FastAPI, которые подменяются в тестах: «сейчас» и настройки."""

from datetime import UTC, datetime

from app.config import Settings


def get_settings() -> Settings:
    """Настройки приложения."""
    return Settings()


def get_now() -> datetime:
    """Текущий момент (UTC); в тестах подменяется фиксированным."""
    return datetime.now(tz=UTC)
