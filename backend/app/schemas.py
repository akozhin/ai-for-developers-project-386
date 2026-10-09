"""Схемы запросов и ответов API (форма данных задаётся контрактом в `api/`)."""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

# Символ NUL запрещён контрактом: PostgreSQL не хранит его в тексте.
NO_NUL = r"^[^\u0000]+$"
# Синтаксис адреса: локальная часть, «@», домен с точкой, без пробелов и NUL.
# Доставляемость не проверяем: контракт требует только формат.
EMAIL = r"^[^@\s\u0000]+@[^@\s\u0000]+\.[^@\s\u0000]+$"

EventTypeId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$"),
]


class EventType(BaseModel):
    """Тип события."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: EventTypeId
    title: Annotated[str, Field(min_length=1, max_length=100, pattern=NO_NUL)]
    description: Annotated[str, Field(min_length=1, max_length=500, pattern=NO_NUL)]
    duration_minutes: Annotated[int, Field(ge=5, le=480)]


class EventTypeList(BaseModel):
    """Список типов событий."""

    items: list[EventType]


class Slot(BaseModel):
    """Свободный интервал времени под тип события (UTC)."""

    model_config = ConfigDict(from_attributes=True)

    starts_at: datetime
    ends_at: datetime


class SlotDay(BaseModel):
    """Свободные слоты одного календарного дня владельца."""

    model_config = ConfigDict(from_attributes=True)

    date: date
    slots: list[Slot]


class SlotsResponse(BaseModel):
    """Окно записи: все 14 дней, начиная с текущей даты."""

    timezone: str
    days: list[SlotDay]


class BookingInput(BaseModel):
    """Данные для бронирования слота (гость)."""

    model_config = ConfigDict(extra="forbid")

    event_type_id: EventTypeId
    starts_at: AwareDatetime
    guest_name: Annotated[str, Field(min_length=1, max_length=100, pattern=NO_NUL)]
    guest_email: Annotated[str, Field(max_length=254, pattern=EMAIL)]
    comment: Annotated[str, Field(max_length=500, pattern=r"^[^\u0000]*$")] | None = None


class Booking(BaseModel):
    """Бронирование (встреча в списке владельца)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: EventType
    starts_at: datetime
    ends_at: datetime
    guest_name: str
    guest_email: str
    comment: str | None = None
    created_at: datetime


class BookingList(BaseModel):
    """Список бронирований."""

    items: list[Booking]
