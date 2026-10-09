"""Точка входа FastAPI-приложения."""

from typing import Any

import yaml
from fastapi import FastAPI

from app.config import Settings
from app.dependencies import get_settings
from app.errors import register_error_handlers
from app.rate_limit import AI_REQUESTS_PER_MINUTE, WINDOW_SECONDS, RateLimiter
from app.routers import bookings, event_types, health, profile, slot_suggestions


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
    application.state.ai_rate_limiter = RateLimiter(AI_REQUESTS_PER_MINUTE, WINDOW_SECONDS)
    register_error_handlers(application)
    application.include_router(health.router)
    application.include_router(event_types.router)
    application.include_router(bookings.router)
    application.include_router(profile.router)
    application.include_router(slot_suggestions.router)
    return application


app = create_app()
