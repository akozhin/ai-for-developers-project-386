"""Конфигурация приложения из переменных окружения."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки процесса; значения читаются из окружения и `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = "INFO"
    openapi_path: Path = Path(__file__).resolve().parents[2] / "api" / "openapi.yaml"
    database_url: str = "postgresql+asyncpg://cal:cal@localhost:5432/cal"
