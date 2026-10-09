"""Точка входа FastAPI-приложения."""

from typing import Any

import yaml
from fastapi import FastAPI

from app.config import Settings
from app.dependencies import get_settings
from app.errors import register_error_handlers
from app.routers import event_types, health


def _load_contract() -> dict[str, Any]:
    """Прочитать закоммиченный контракт (api/openapi.yaml, генерируется из TypeSpec)."""
    contract: dict[str, Any] = yaml.safe_load(Settings().openapi_path.read_text(encoding="utf-8"))
    return contract


def create_app() -> FastAPI:
    """Собрать приложение."""
    get_settings.cache_clear()
    get_settings()  # fail-fast: некорректная конфигурация останавливает запуск
    application = FastAPI(title="Запись на звонок")
    application.openapi = _load_contract  # type: ignore[method-assign]
    register_error_handlers(application)
    application.include_router(health.router)
    application.include_router(event_types.router)
    return application


app = create_app()
