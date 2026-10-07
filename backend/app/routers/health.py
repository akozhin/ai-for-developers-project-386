"""Служебный эндпоинт проверки работоспособности."""

from fastapi import APIRouter

router = APIRouter(tags=["service"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Вернуть признак живого процесса."""
    return {"status": "ok"}
