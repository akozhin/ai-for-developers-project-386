"""Конфигурация приложения из переменных окружения (fail-fast: ошибка — приложение не стартует)."""

from datetime import time
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
SLOT_GRID_MINUTES = 30


class Settings(BaseSettings):
    """Настройки процесса; значения читаются из окружения и `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = "INFO"
    openapi_path: Path = Path(__file__).resolve().parents[2] / "api" / "openapi.yaml"
    database_url: str = "postgresql+asyncpg://cal:cal@localhost:5432/cal"

    # Рабочее расписание владельца: одно на все типы событий.
    owner_timezone: str = "Europe/Moscow"
    work_days: Annotated[list[str], NoDecode] = ["mon", "tue", "wed", "thu", "fri"]
    work_start: time = time(10, 0)
    work_end: time = time(18, 0)
    booking_min_notice_minutes: int = Field(default=120, ge=0)

    @field_validator("owner_timezone")
    @classmethod
    def _timezone_must_be_iana(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            message = f"неизвестный часовой пояс IANA: {value}"
            raise ValueError(message) from error
        return value

    @field_validator("work_days", mode="before")
    @classmethod
    def _parse_work_days(cls, value: Any) -> list[str]:  # noqa: ANN401
        raw = value.split(",") if isinstance(value, str) else list(value)
        days = list(dict.fromkeys(str(day).strip().lower() for day in raw if str(day).strip()))
        unknown = [day for day in days if day not in WEEKDAYS]
        if not days or unknown:
            allowed = ", ".join(WEEKDAYS)
            message = (
                f"WORK_DAYS: нужен хотя бы один день из {allowed}, получено {unknown or 'пусто'}"
            )
            raise ValueError(message)
        return days

    @model_validator(mode="after")
    def _schedule_must_be_consistent(self) -> "Settings":
        for name, value in (("WORK_START", self.work_start), ("WORK_END", self.work_end)):
            if value.minute % SLOT_GRID_MINUTES or value.second or value.microsecond:
                message = f"{name} должен быть кратен {SLOT_GRID_MINUTES} минутам"
                raise ValueError(message)
        if self.work_start >= self.work_end:
            message = "WORK_START должен быть раньше WORK_END"
            raise ValueError(message)
        return self
