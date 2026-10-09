"""Подключение к PostgreSQL: базовый класс моделей и сессия на запрос."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import Settings


class Base(DeclarativeBase):
    """Базовый класс ORM-моделей."""


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Создать фабрику сессий по настройкам приложения (один раз на процесс)."""
    engine = create_async_engine(Settings().database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Зависимость FastAPI: сессия БД на время запроса."""
    async with get_sessionmaker()() as session:
        yield session
