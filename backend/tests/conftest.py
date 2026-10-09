"""Общие фикстуры: реальная PostgreSQL и чистое состояние на каждый тест."""

import asyncio
import os
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from pydantic_settings import SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.db import get_session
from app.dependencies import get_now, get_settings
from app.main import create_app


class IsolatedSettings(Settings):
    """Настройки без чтения `.env`: результат тестов не зависит от файла разработчика."""

    model_config = SettingsConfigDict(env_file=None)


ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
TEST_DATABASE_URL = os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://cal:cal@localhost:5432/cal_test",
)


async def _ensure_database_exists(url: str) -> None:
    """Создать тестовую БД, если её ещё нет."""
    parsed = make_url(url)
    admin = create_async_engine(parsed.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as connection:
            exists = await connection.scalar(
                text("select 1 from pg_database where datname = :name"),
                {"name": parsed.database},
            )
            if not exists:
                quoted = connection.dialect.identifier_preparer.quote(str(parsed.database))
                await connection.execute(text(f"create database {quoted}"))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session")
def database_url() -> str:
    """Тестовая БД с применёнными миграциями (один раз на прогон)."""
    if not str(make_url(TEST_DATABASE_URL).database).endswith("_test"):
        message = (
            "TEST_DATABASE_URL должен указывать на БД с суффиксом _test: тесты очищают все таблицы"
        )
        raise RuntimeError(message)
    asyncio.run(_ensure_database_exists(TEST_DATABASE_URL))
    alembic_config = Config(str(ALEMBIC_INI))
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("%", "%%"))
    command.upgrade(alembic_config, "head")
    return TEST_DATABASE_URL


async def _truncate_all_tables(engine: AsyncEngine) -> None:
    """Очистить все таблицы данных, кроме служебной таблицы версий Alembic."""
    async with engine.begin() as connection:
        tables = (
            (
                await connection.execute(
                    text(
                        "select quote_ident(tablename) from pg_tables "
                        "where schemaname = 'public' and tablename <> 'alembic_version'",
                    ),
                )
            )
            .scalars()
            .all()
        )
        if tables:
            await connection.execute(
                text(f"truncate {', '.join(tables)} restart identity cascade"),
            )


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Движок на тест; данные очищаются до и после теста (упавший прогон не мешает)."""
    test_engine = create_async_engine(database_url)
    try:
        await _truncate_all_tables(test_engine)
        yield test_engine
    finally:
        await _truncate_all_tables(test_engine)
        await test_engine.dispose()


@pytest.fixture(scope="module")
def clean_database(database_url: str) -> Iterator[None]:
    """Очистка данных до и после модуля с синхронными тестами (Schemathesis)."""

    async def reset() -> None:
        engine = create_async_engine(database_url, poolclass=NullPool)
        try:
            await _truncate_all_tables(engine)
        finally:
            await engine.dispose()

    asyncio.run(reset())
    yield
    asyncio.run(reset())


@pytest.fixture
def app(engine: AsyncEngine) -> FastAPI:
    """Приложение, которое работает с тестовой БД."""
    application = create_app()
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    # Лямбда нужна: класс FastAPI принял бы за зависимость с параметрами запроса.
    application.dependency_overrides[get_settings] = lambda: IsolatedSettings()  # noqa: PLW0108
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP-клиент поверх ASGI без поднятия сервера."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def freeze_now(app: FastAPI) -> Callable[[str], None]:
    """Зафиксировать «сейчас» (ISO 8601 с часовым поясом) для запросов к приложению."""

    def freeze(moment: str) -> None:
        frozen = datetime.fromisoformat(moment)
        assert frozen.tzinfo is not None, "«сейчас» в тестах задаётся с часовым поясом"
        app.dependency_overrides[get_now] = lambda: frozen

    return freeze


@pytest.fixture
def configure_settings(app: FastAPI) -> Callable[..., None]:
    """Подменить настройки приложения (поля `Settings`): расписание, профиль, ключ AI."""

    def configure(**fields: Any) -> None:  # noqa: ANN401
        app.dependency_overrides[get_settings] = lambda: IsolatedSettings(**fields)

    return configure


@pytest.fixture
def configure_schedule(configure_settings: Callable[..., None]) -> Callable[..., None]:
    """То же, что `configure_settings`; имя для тестов расписания и запаса до записи."""
    return configure_settings
