"""Типы событий: создание владельцем, чтение гостем и владельцем."""

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session
from app.errors import ApiError

router = APIRouter(prefix="/api/v1/event-types", tags=["event-types"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("")
async def list_event_types(session: SessionDep) -> schemas.EventTypeList:
    """Вернуть все типы событий по возрастанию длительности."""
    rows = await session.scalars(
        select(models.EventType).order_by(models.EventType.duration_minutes, models.EventType.id),
    )
    return schemas.EventTypeList(
        items=[schemas.EventType.model_validate(row) for row in rows],
    )


@router.post("", status_code=HTTPStatus.CREATED)
async def create_event_type(body: schemas.EventType, session: SessionDep) -> schemas.EventType:
    """Создать тип события; id уникален."""
    session.add(models.EventType(**body.model_dump()))
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise ApiError(
            HTTPStatus.CONFLICT,
            "event_type_exists",
            "Тип события с таким id уже существует",
        ) from error
    return body


@router.get("/{event_type_id}")
async def get_event_type(event_type_id: str, session: SessionDep) -> schemas.EventType:
    """Вернуть один тип события; неизвестный или некорректный id — `404`."""
    event_type = await session.get(models.EventType, event_type_id)
    if event_type is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "event_type_not_found", "Тип события не найден")
    return schemas.EventType.model_validate(event_type)
