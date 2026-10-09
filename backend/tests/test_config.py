"""Конфигурация рабочего расписания: значения по умолчанию и fail-fast при ошибках."""

from datetime import time

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app


def test_default_schedule_is_weekdays_ten_to_eighteen_in_moscow() -> None:
    settings = Settings()

    assert settings.owner_timezone == "Europe/Moscow"
    assert settings.work_days == ["mon", "tue", "wed", "thu", "fri"]
    assert (settings.work_start, settings.work_end) == (time(10, 0), time(18, 0))
    assert settings.booking_min_notice_minutes == 120  # noqa: PLR2004


def test_schedule_is_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OWNER_TIMEZONE", "Asia/Yekaterinburg")
    monkeypatch.setenv("WORK_DAYS", "sat, sun")
    monkeypatch.setenv("WORK_START", "09:30")
    monkeypatch.setenv("WORK_END", "13:00")
    monkeypatch.setenv("BOOKING_MIN_NOTICE_MINUTES", "0")

    settings = Settings()

    assert settings.owner_timezone == "Asia/Yekaterinburg"
    assert settings.work_days == ["sat", "sun"]
    assert (settings.work_start, settings.work_end) == (time(9, 30), time(13, 0))
    assert settings.booking_min_notice_minutes == 0


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OWNER_TIMEZONE", "Mars/Olympus"),
        ("WORK_DAYS", "mon,funday"),
        ("WORK_DAYS", ""),
        ("WORK_START", "10:15"),
        ("WORK_END", "17:50"),
        ("WORK_START", "18:00"),
        ("WORK_START", "19:00"),
        ("BOOKING_MIN_NOTICE_MINUTES", "-1"),
    ],
)
def test_invalid_schedule_stops_application_startup(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        create_app()
