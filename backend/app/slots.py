"""Расчёт свободных слотов: одна функция для выдачи слотов, проверки бронирования и AI."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.config import SLOT_GRID_MINUTES, WEEKDAYS, Settings

WINDOW_DAYS = 14

Interval = tuple[datetime, datetime]


@dataclass(frozen=True)
class Slot:
    """Свободный интервал под тип события (время в UTC)."""

    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class SlotDay:
    """Свободные слоты одного календарного дня владельца."""

    date: date
    slots: list[Slot]


def window_dates(now: datetime, settings: Settings) -> list[date]:
    """Даты окна записи: сегодня по календарю владельца и ещё 13 дней."""
    today = now.astimezone(ZoneInfo(settings.owner_timezone)).date()
    return [today + timedelta(days=offset) for offset in range(WINDOW_DAYS)]


def window_bounds(now: datetime, settings: Settings) -> Interval:
    """Границы окна записи в UTC: от начала первого дня до конца последнего."""
    zone = ZoneInfo(settings.owner_timezone)
    dates = window_dates(now, settings)
    start = datetime.combine(dates[0], time.min, zone)
    end = datetime.combine(dates[-1] + timedelta(days=1), time.min, zone)
    return start.astimezone(UTC), end.astimezone(UTC)


def compute_slot_days(
    *,
    duration_minutes: int,
    now: datetime,
    settings: Settings,
    busy: Sequence[Interval],
) -> list[SlotDay]:
    """Свободные слоты на все дни окна записи.

    Слот начинается на сетке 30 минут, целиком лежит в рабочем интервале дня, начинается не
    раньше «сейчас» плюс запас до записи и не пересекается (по полуинтервалам) с занятым временем.
    """
    zone = ZoneInfo(settings.owner_timezone)
    duration = timedelta(minutes=duration_minutes)
    earliest = now + timedelta(minutes=settings.booking_min_notice_minutes)
    working_weekdays = {WEEKDAYS.index(day) for day in settings.work_days}
    step = timedelta(minutes=SLOT_GRID_MINUTES)

    days: list[SlotDay] = []
    for day in window_dates(now, settings):
        slots: list[Slot] = []
        if day.weekday() in working_weekdays:
            opens = datetime.combine(day, settings.work_start, zone)
            closes = datetime.combine(day, settings.work_end, zone)
            start = opens
            while start + duration <= closes:
                slot = Slot(start.astimezone(UTC), (start + duration).astimezone(UTC))
                if slot.starts_at >= earliest and not _overlaps_any(slot, busy):
                    slots.append(slot)
                start += step
        days.append(SlotDay(date=day, slots=slots))
    return days


def _overlaps_any(slot: Slot, busy: Sequence[Interval]) -> bool:
    return any(begins < slot.ends_at and slot.starts_at < ends for begins, ends in busy)
