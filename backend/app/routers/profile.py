"""Профиль владельца для шапки главного экрана."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app import schemas
from app.config import Settings
from app.dependencies import get_settings

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("")
async def get_profile(settings: Annotated[Settings, Depends(get_settings)]) -> schemas.Profile:
    """Вернуть имя, часовой пояс и аватар владельца и признак доступности AI."""
    return schemas.Profile(
        name=settings.owner_name,
        timezone=settings.owner_timezone,
        avatar_url=settings.owner_avatar_url,
        ai_enabled=settings.ai_enabled,
    )
