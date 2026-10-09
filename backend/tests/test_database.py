"""Приложение работает с реальной PostgreSQL через зависимость сессии."""

from typing import Annotated

import httpx
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session


async def test_session_dependency_reaches_postgres(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    async def probe(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, int]:
        value = (await session.execute(text("select 41 + 1"))).scalar_one()
        return {"value": value}

    app.add_api_route("/__probe", probe)

    response = await client.get("/__probe")

    assert response.json() == {"value": 42}
