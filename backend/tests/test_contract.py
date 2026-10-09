"""Ответы backend соответствуют контракту (Schemathesis по `api/openapi.yaml`)."""

import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
import schemathesis
from schemathesis import Case
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import get_session
from app.main import create_app


async def _session_per_request() -> AsyncIterator[AsyncSession]:
    """Сессия тестовой БД; движок на запрос: Schemathesis шлёт запросы из разных потоков."""
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"], poolclass=NullPool)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()


contract_app = create_app()
contract_app.dependency_overrides[get_session] = _session_per_request
schema = schemathesis.openapi.from_asgi("/openapi.json", contract_app)

# Маршруты, которых ещё нет в коде (слоты, бронирования, профиль, AI), добавляются по мере тикетов.
IMPLEMENTED = r"^/(health|api/v1/event-types(/\{id\})?)$"


@schema.include(path_regex=IMPLEMENTED).parametrize()
@pytest.mark.usefixtures("clean_database")
def test_implemented_endpoints_match_contract(case: Case[Any]) -> None:
    case.call_and_validate()
