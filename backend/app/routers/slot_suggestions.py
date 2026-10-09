"""AI-подбор слотов по пожеланию гостя."""

from collections.abc import Callable
from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.availability import load_free_days
from app.config import Settings
from app.db import get_session
from app.dependencies import get_chat_model_factory, get_now, get_settings
from app.errors import ApiError
from app.rate_limit import limit_ai_requests
from app.slot_agent import suggest_slots

router = APIRouter(
    prefix="/api/v1/slot-suggestions",
    tags=["slot-suggestions"],
    dependencies=[Depends(limit_ai_requests)],
)


@router.post("")
async def create_slot_suggestion(
    body: schemas.SlotSuggestionInput,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    now: Annotated[datetime, Depends(get_now)],
    model_factory: Annotated[Callable[[Settings], BaseChatModel], Depends(get_chat_model_factory)],
) -> schemas.SlotSuggestionResponse:
    """Подобрать до трёх свободных слотов по тексту гостя."""
    if not settings.ai_enabled:
        raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "ai_unavailable", "AI-подбор недоступен")
    event_type = await session.get(models.EventType, body.event_type_id)
    if event_type is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "event_type_not_found", "Тип события не найден")
    free_days = await load_free_days(session, event_type, now, settings)
    return await suggest_slots(
        model=model_factory(settings),
        free_days=free_days,
        text=body.text,
        zone=ZoneInfo(body.timezone),
        now=now,
        duration_minutes=event_type.duration_minutes,
    )
