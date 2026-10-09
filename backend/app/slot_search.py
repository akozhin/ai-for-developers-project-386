"""Внутренний поиск слотов для AI-агента (в контракт не входит), поверх функции слотов."""

from collections.abc import Collection
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.config import WEEKDAYS
from app.slots import Slot, SlotDay

MAX_FOUND_SLOTS = 20


def find_slots(  # noqa: PLR0913
    days: list[SlotDay],
    *,
    guest_zone: ZoneInfo,
    date_from: date | None = None,
    date_to: date | None = None,
    weekdays: Collection[str] | None = None,
    time_from: time | None = None,
    time_to: time | None = None,
    limit: int = MAX_FOUND_SLOTS,
) -> list[Slot]:
    """Свободные слоты по возрастанию, не больше 20.

    Даты, дни недели и интервал времени трактуются в часовом поясе гостя; слот должен
    начинаться не раньше `time_from` и заканчиваться не позже `time_to`.
    """
    wanted_days = {WEEKDAYS.index(day) for day in weekdays} if weekdays else None
    found: list[Slot] = []
    for slot in sorted((slot for day in days for slot in day.slots), key=lambda s: s.starts_at):
        starts = slot.starts_at.astimezone(guest_zone)
        if _matches(slot, starts, guest_zone, date_from, date_to, wanted_days, time_from, time_to):
            found.append(slot)
            if len(found) >= min(max(limit, 1), MAX_FOUND_SLOTS):
                break
    return found


def _matches(  # noqa: PLR0913, PLR0917
    slot: Slot,
    starts: datetime,
    zone: ZoneInfo,
    date_from: date | None,
    date_to: date | None,
    weekdays: set[int] | None,
    time_from: time | None,
    time_to: time | None,
) -> bool:
    if (date_from and starts.date() < date_from) or (date_to and starts.date() > date_to):
        return False
    if weekdays is not None and starts.weekday() not in weekdays:
        return False
    if time_from and starts.timetz().replace(tzinfo=None) < time_from:
        return False
    return not (time_to and slot.ends_at > datetime.combine(starts.date(), time_to, zone))
