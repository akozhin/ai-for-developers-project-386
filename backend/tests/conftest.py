"""Общие фикстуры: реальная PostgreSQL и чистое состояние на каждый тест."""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db import get_session
from app.main import create_app

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
TEST_DATABASE_URL = os.environ.get(
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
                await connection.execute(text(f'create database "{parsed.database}"'))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Тестовая БД с применёнными миграциями (один раз на прогон)."""
    asyncio.run(_ensure_database_exists(TEST_DATABASE_URL))
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    try:
        command.upgrade(Config(str(ALEMBIC_INI)), "head")
        yield TEST_DATABASE_URL
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Движок на тест; после теста все таблицы данных очищаются."""
    test_engine = create_async_engine(database_url)
    try:
        yield test_engine
    finally:
        async with test_engine.begin() as connection:
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
        await test_engine.dispose()


@pytest.fixture
def app(engine: AsyncEngine) -> FastAPI:
    """Приложение, которое работает с тестовой БД."""
    application = create_app()
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP-клиент поверх ASGI без поднятия сервера."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
