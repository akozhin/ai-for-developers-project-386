"""Слоты типа события: окно из 14 дней, сетка 30 минут, рабочее расписание, запас до записи."""

from collections.abc import Callable
from datetime import datetime
from http import HTTPStatus
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app import models

CALL_30 = {
    "id": "call-30",
    "title": "Звонок 30 минут",
    "description": "Короткий созвон",
    "duration_minutes": 30,
}
CALL_60 = {**CALL_30, "id": "call-60", "title": "Звонок 60 минут", "duration_minutes": 60}
SLOTS_URL = "/api/v1/event-types/{}/slots"
# Понедельник 2026-10-12, 09:00 по Москве (UTC+3).
MONDAY_MORNING = "2026-10-12T06:00:00+00:00"


def slot(starts: str, ends: str) -> dict[str, str]:
    return {"starts_at": starts, "ends_at": ends}


async def get_days(client: httpx.AsyncClient, event_type_id: str) -> list[dict[str, Any]]:
    response = await client.get(SLOTS_URL.format(event_type_id))
    assert response.status_code == HTTPStatus.OK
    return response.json()["days"]  # type: ignore[no-any-return]


async def test_unknown_event_type_returns_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get(SLOTS_URL.format("call-45"))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "event_type_not_found"


async def test_window_has_fourteen_days_from_today_in_owner_timezone(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    response = await client.get(SLOTS_URL.format("call-30"))

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["timezone"] == "Europe/Moscow"
    assert [day["date"] for day in body["days"]] == [
        "2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17",
        "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23",
        "2026-10-24", "2026-10-25",
    ]  # fmt: skip


async def test_working_day_has_half_hour_slots_inside_working_hours(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    monday = (await get_days(client, "call-30"))[0]["slots"]

    assert len(monday) == 16  # 10:00–18:00 по полчаса  # noqa: PLR2004
    assert monday[0] == slot("2026-10-12T07:00:00Z", "2026-10-12T07:30:00Z")
    assert monday[-1] == slot("2026-10-12T14:30:00Z", "2026-10-12T15:00:00Z")


async def test_sixty_minute_event_never_starts_at_half_past_five(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_60)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    monday = (await get_days(client, "call-60"))[0]["slots"]

    assert len(monday) == 15  # 10:00…17:00 по полчаса  # noqa: PLR2004
    assert monday[-1] == slot("2026-10-12T14:00:00Z", "2026-10-12T15:00:00Z")
    assert "2026-10-12T14:30:00Z" not in [item["starts_at"] for item in monday]


async def test_slots_before_now_plus_notice_are_not_offered(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(
        "2026-10-12T07:15:00+00:00"
    )  # понедельник 10:15 по Москве, запас по умолчанию 2 часа

    monday = (await get_days(client, "call-30"))[0]["slots"]

    assert monday[0] == slot("2026-10-12T09:30:00Z", "2026-10-12T10:00:00Z")  # 12:30, а не 12:15


async def test_without_notice_next_grid_slot_after_now_is_offered(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now("2026-10-12T07:15:00+00:00")
    configure_schedule(booking_min_notice_minutes=0)

    monday = (await get_days(client, "call-30"))[0]["slots"]

    assert monday[0] == slot("2026-10-12T07:30:00Z", "2026-10-12T08:00:00Z")  # 10:30


async def test_slot_starting_exactly_at_the_earliest_moment_is_offered(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now("2026-10-12T08:00:00+00:00")  # 11:00 по Москве
    configure_schedule(booking_min_notice_minutes=0)

    monday = (await get_days(client, "call-30"))[0]["slots"]

    assert monday[0] == slot("2026-10-12T08:00:00Z", "2026-10-12T08:30:00Z")


async def test_today_is_present_but_empty_after_working_hours(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now("2026-10-12T17:00:00+00:00")  # понедельник 20:00 по Москве

    days = await get_days(client, "call-30")

    assert len(days) == 14  # noqa: PLR2004
    assert days[0] == {"date": "2026-10-12", "slots": []}
    assert days[1]["slots"][0] == slot(
        "2026-10-13T07:00:00Z", "2026-10-13T07:30:00Z"
    )  # вторник 10:00


async def test_weekend_days_are_empty_and_weekdays_are_not(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    days = await get_days(client, "call-30")

    by_date = {day["date"]: day["slots"] for day in days}
    assert by_date["2026-10-17"] == [] == by_date["2026-10-18"]  # суббота и воскресенье
    assert len(by_date["2026-10-16"]) == 16  # пятница  # noqa: PLR2004
    assert len(by_date["2026-10-19"]) == 16  # понедельник  # noqa: PLR2004


async def test_window_starts_on_the_owner_calendar_day_not_the_utc_day(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now("2026-10-12T22:30:00+00:00")  # 13 октября, 01:30 по Москве

    days = await get_days(client, "call-30")

    assert days[0]["date"] == "2026-10-13"
    assert days[-1]["date"] == "2026-10-26"


async def test_custom_timezone_days_and_hours_are_applied(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(
        owner_timezone="Asia/Yekaterinburg",  # UTC+5
        work_days=["tue", "thu"],
        work_start="09:30",
        work_end="11:00",
        booking_min_notice_minutes=0,
    )

    response = await client.get(SLOTS_URL.format("call-30"))

    by_date = {day["date"]: day["slots"] for day in response.json()["days"]}
    assert response.json()["timezone"] == "Asia/Yekaterinburg"
    assert by_date["2026-10-13"] == [  # вторник
        slot("2026-10-13T04:30:00Z", "2026-10-13T05:00:00Z"),
        slot("2026-10-13T05:00:00Z", "2026-10-13T05:30:00Z"),
        slot("2026-10-13T05:30:00Z", "2026-10-13T06:00:00Z"),
    ]
    assert by_date["2026-10-14"] == []  # среда


async def insert_booking(
    engine: AsyncEngine,
    event_type_id: str,
    starts_at: str,
    ends_at: str,
) -> None:
    """Вставить бронирование напрямую в БД (создание через API — отдельный тикет)."""
    async with async_sessionmaker(engine)() as session:
        session.add(
            models.Booking(
                event_type_id=event_type_id,
                starts_at=datetime.fromisoformat(starts_at),
                ends_at=datetime.fromisoformat(ends_at),
                guest_name="Анна",
                guest_email="anna@example.com",
            ),
        )
        await session.commit()


def starts(day: dict[str, Any]) -> list[str]:
    return [item["starts_at"] for item in day["slots"]]


async def test_booking_of_another_type_hides_every_overlapping_slot(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    await client.post("/api/v1/event-types", json=CALL_60)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)
    # Звонок на 60 минут в понедельник 12:00–13:00 по Москве.
    await insert_booking(
        engine, "call-60", "2026-10-12T09:00:00+00:00", "2026-10-12T10:00:00+00:00"
    )

    monday = (await get_days(client, "call-30"))[0]

    assert "2026-10-12T09:00:00Z" not in starts(monday)  # 12:00
    assert "2026-10-12T09:30:00Z" not in starts(monday)  # 12:30
    assert "2026-10-12T08:30:00Z" in starts(monday)  # 11:30–12:00 встык — свободно
    assert "2026-10-12T10:00:00Z" in starts(monday)  # 13:00 встык — свободно


async def test_sixty_minute_slots_overlapping_a_short_booking_are_hidden(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    await client.post("/api/v1/event-types", json=CALL_60)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)
    # Звонок на 30 минут в понедельник 12:00–12:30 по Москве.
    await insert_booking(
        engine, "call-30", "2026-10-12T09:00:00+00:00", "2026-10-12T09:30:00+00:00"
    )

    monday = (await get_days(client, "call-60"))[0]

    assert "2026-10-12T08:30:00Z" not in starts(monday)  # 11:30–12:30 пересекается
    assert "2026-10-12T09:00:00Z" not in starts(monday)  # 12:00–13:00 пересекается
    assert "2026-10-12T08:00:00Z" in starts(monday)  # 11:00–12:00 встык — свободно
    assert "2026-10-12T09:30:00Z" in starts(monday)  # 12:30–13:30 встык — свободно


async def test_booking_of_the_same_type_hides_its_own_slot(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)
    await insert_booking(
        engine, "call-30", "2026-10-12T07:00:00+00:00", "2026-10-12T07:30:00+00:00"
    )

    monday = (await get_days(client, "call-30"))[0]

    assert starts(monday)[0] == "2026-10-12T07:30:00Z"
    assert len(monday["slots"]) == 15  # noqa: PLR2004


async def test_day_of_daylight_saving_change_counts_real_elapsed_time(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now("2026-10-24T10:00:00+00:00")
    # 25 октября 2026 в Берлине переводят часы назад: интервал 01:00–04:00 длится четыре часа.
    configure_schedule(
        owner_timezone="Europe/Berlin",
        work_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        work_start="01:00",
        work_end="04:00",
        booking_min_notice_minutes=0,
    )

    change_day = (await get_days(client, "call-30"))[1]

    assert change_day["date"] == "2026-10-25"
    assert len(change_day["slots"]) == 8  # noqa: PLR2004
    assert change_day["slots"][0] == slot("2026-10-24T23:00:00Z", "2026-10-24T23:30:00Z")
    assert change_day["slots"][-1] == slot("2026-10-25T02:30:00Z", "2026-10-25T03:00:00Z")


async def test_both_durations_use_the_same_grid_but_fit_differently(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    await client.post("/api/v1/event-types", json=CALL_60)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    short = (await get_days(client, "call-30"))[0]
    long = (await get_days(client, "call-60"))[0]

    assert len(short["slots"]) == 16  # noqa: PLR2004
    assert len(long["slots"]) == 15  # noqa: PLR2004
    assert set(starts(long)) < set(starts(short))
