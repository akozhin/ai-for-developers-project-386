"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    """Собрать приложение."""
    application = FastAPI(title="Запись на звонок")
    application.include_router(health.router)
    return application


app = create_app()
