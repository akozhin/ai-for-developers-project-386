"""Свободные слоты типа события с учётом бронирований (общее для выдачи слотов и AI)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, slots
from app.config import Settings


async def load_free_days(
    session: AsyncSession,
    event_type: models.EventType,
    now: datetime,
    settings: Settings,
) -> list[slots.SlotDay]:
    """Свободные слоты типа события на все дни окна записи."""
    window_start, window_end = slots.window_bounds(now, settings)
    busy = await session.execute(
        select(models.Booking.starts_at, models.Booking.ends_at).where(
            models.Booking.starts_at < window_end,
            models.Booking.ends_at > window_start,
        ),
    )
    return slots.compute_slot_days(
        duration_minutes=event_type.duration_minutes,
        now=now,
        settings=settings,
        busy=[(begins, ends) for begins, ends in busy],
    )
