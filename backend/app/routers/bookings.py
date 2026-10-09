"""Бронирования: гость занимает слот, владелец смотрит предстоящие встречи."""

from datetime import datetime
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, slots
from app.config import Settings
from app.db import get_session
from app.dependencies import get_now, get_settings
from app.errors import ApiError

EXCLUSION_VIOLATION = "23P01"  # SQLSTATE: нарушение ограничения EXCLUDE (пересечение броней)

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _slot_taken() -> ApiError:
    return ApiError(HTTPStatus.CONFLICT, "slot_taken", "Слот только что заняли")


async def _overlaps_existing_booking(session: AsyncSession, slot: slots.Slot) -> bool:
    """Быстрая проверка пересечения; окончательный арбитр — ограничение БД."""
    overlaps = exists().where(
        models.Booking.starts_at < slot.ends_at,
        models.Booking.ends_at > slot.starts_at,
    )
    return bool(await session.scalar(select(overlaps)))


@router.post("", status_code=HTTPStatus.CREATED, response_model_exclude_none=True)
async def create_booking(
    body: schemas.BookingInput,
    session: SessionDep,
    settings: Annotated[Settings, Depends(get_settings)],
    now: Annotated[datetime, Depends(get_now)],
) -> schemas.Booking:
    """Забронировать слот: поля, затем тип события, затем время (недоступно или занято)."""
    event_type = await session.get(models.EventType, body.event_type_id)
    if event_type is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "event_type_not_found", "Тип события не найден")
    slot = slots.find_bookable_slot(
        duration_minutes=event_type.duration_minutes,
        starts_at=body.starts_at,
        now=now,
        settings=settings,
    )
    if slot is None:
        raise ApiError(
            HTTPStatus.CONFLICT,
            "slot_not_available",
            "Время недоступно, выберите другое",
        )
    if await _overlaps_existing_booking(session, slot):
        raise _slot_taken()

    booking = models.Booking(
        event_type=event_type,
        starts_at=slot.starts_at,
        ends_at=slot.ends_at,
        guest_name=body.guest_name,
        guest_email=body.guest_email,
        comment=body.comment,
        created_at=now,
    )
    session.add(booking)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if getattr(error.orig, "sqlstate", None) != EXCLUSION_VIOLATION:
            raise
        # Арбитр — ограничение БД: так проигрывает второй из двух одновременных запросов.
        raise _slot_taken() from error
    return schemas.Booking.model_validate(booking)


@router.get("", response_model_exclude_none=True)
async def list_bookings(
    session: SessionDep,
    now: Annotated[datetime, Depends(get_now)],
) -> schemas.BookingList:
    """Предстоящие встречи всех типов по возрастанию начала."""
    rows = await session.scalars(
        select(models.Booking)
        .where(models.Booking.starts_at >= now)
        .order_by(models.Booking.starts_at, models.Booking.id),
    )
    return schemas.BookingList(items=[schemas.Booking.model_validate(row) for row in rows])
