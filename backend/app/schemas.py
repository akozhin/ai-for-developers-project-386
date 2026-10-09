"""Схемы запросов и ответов API (форма данных задаётся контрактом в `api/`)."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

EventTypeId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$"),
]


class EventType(BaseModel):
    """Тип события."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: EventTypeId
    title: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    duration_minutes: Annotated[int, Field(ge=5, le=480)]


class EventTypeList(BaseModel):
    """Список типов событий."""

    items: list[EventType]
