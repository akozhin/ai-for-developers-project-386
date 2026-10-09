"""Бронирования: создание гостем, список предстоящих встреч владельца, защита от пересечений."""

import asyncio
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from app.routers import bookings

CALL_30 = {
    "id": "call-30",
    "title": "Звонок 30 минут",
    "description": "Короткий созвон",
    "duration_minutes": 30,
}
CALL_60 = {**CALL_30, "id": "call-60", "title": "Звонок 60 минут", "duration_minutes": 60}
# Понедельник 2026-10-12, 09:00 по Москве (UTC+3); запас до записи 0, поэтому 10:00 уже доступно.
MONDAY_MORNING = "2026-10-12T06:00:00+00:00"
# Слот понедельника 12:00–12:30 по Москве.
NOON = "2026-10-12T09:00:00Z"


def booking(starts_at: str = NOON, event_type_id: str = "call-30", **fields: Any) -> dict[str, Any]:  # noqa: ANN401
    return {
        "event_type_id": event_type_id,
        "starts_at": starts_at,
        "guest_name": "Анна",
        "guest_email": "anna@example.com",
        **fields,
    }


async def post(client: httpx.AsyncClient, body: dict[str, Any]) -> httpx.Response:
    return await client.post("/api/v1/bookings", json=body)


async def test_created_booking_is_returned_and_listed_for_the_owner(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=0)

    created = await post(client, booking(comment="Хочу обсудить проект"))
    listed = await client.get("/api/v1/bookings")

    expected = {
        "event_type": CALL_30,
        "starts_at": "2026-10-12T09:00:00Z",
        "ends_at": "2026-10-12T09:30:00Z",
        "guest_name": "Анна",
        "guest_email": "anna@example.com",
        "comment": "Хочу обсудить проект",
        "created_at": "2026-10-12T06:00:00Z",
    }
    assert created.status_code == HTTPStatus.CREATED
    assert {key: value for key, value in created.json().items() if key != "id"} == expected
    assert listed.status_code == HTTPStatus.OK
    assert [{k: v for k, v in item.items() if k != "id"} for item in listed.json()["items"]] == [
        expected,
    ]
    assert listed.json()["items"][0]["id"] == created.json()["id"]


async def prepare(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
    *,
    notice: int = 0,
) -> None:
    """Два типа событий, понедельник 09:00 по Москве, запас до записи `notice` минут."""
    await client.post("/api/v1/event-types", json=CALL_30)
    await client.post("/api/v1/event-types", json=CALL_60)
    freeze_now(MONDAY_MORNING)
    configure_schedule(booking_min_notice_minutes=notice)


async def booking_ids(client: httpx.AsyncClient) -> list[str]:
    response = await client.get("/api/v1/bookings")
    return [item["starts_at"] for item in response.json()["items"]]


# ───────────────────────── 422: поля ─────────────────────────


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"unexpected": "лишнее"}, "unexpected"),
        ({"guest_email": "не-email"}, "guest_email"),
        ({"guest_email": "anna@localhost"}, "guest_email"),
        ({"guest_email": "a" * 250 + "@example.com"}, "guest_email"),
        ({"guest_name": ""}, "guest_name"),
        ({"guest_name": "и" * 101}, "guest_name"),
        ({"guest_name": "до\x00после"}, "guest_name"),
        ({"comment": "к" * 501}, "comment"),
        ({"comment": "до\x00после"}, "comment"),
        ({"starts_at": "2026-10-12T12:00:00"}, "starts_at"),  # без часового пояса
        ({"starts_at": "послезавтра"}, "starts_at"),
        ({"event_type_id": "Call_30"}, "event_type_id"),
    ],
)
async def test_invalid_fields_return_validation_error(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
    changes: dict[str, object],
    field: str,
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    response = await post(client, {**booking(), **changes})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"
    assert field in [item["field"] for item in response.json()["fields"]]


@pytest.mark.parametrize("missing", ["event_type_id", "starts_at", "guest_name", "guest_email"])
async def test_missing_required_field_returns_validation_error(
    client: httpx.AsyncClient,
    missing: str,
) -> None:
    body = {key: value for key, value in booking().items() if key != missing}

    response = await post(client, body)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [item["field"] for item in response.json()["fields"]] == [missing]


async def test_field_errors_are_reported_before_the_unknown_event_type(
    client: httpx.AsyncClient,
) -> None:
    response = await post(client, booking(event_type_id="call-45", guest_email="не-email"))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_comment_is_optional_and_omitted_from_the_response(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    response = await post(client, booking())

    assert response.status_code == HTTPStatus.CREATED
    assert "comment" not in response.json()


# ───────────────────────── 404 ─────────────────────────


async def test_unknown_event_type_returns_not_found(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    response = await post(client, booking(event_type_id="call-45"))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "event_type_not_found"


# ───────────────────────── 409 slot_not_available ─────────────────────────


@pytest.mark.parametrize(
    ("event_type_id", "starts_at"),
    [
        ("call-30", "2026-10-12T09:15:00Z"),  # не на сетке 30 минут
        ("call-30", "2026-10-12T06:30:00Z"),  # до начала рабочего дня (09:30)
        ("call-30", "2026-10-12T15:00:00Z"),  # после конца рабочего дня (18:00)
        ("call-60", "2026-10-12T14:30:00Z"),  # 17:30 + 60 минут не помещается
        ("call-30", "2026-10-17T09:00:00Z"),  # суббота
        ("call-30", "2026-10-26T09:00:00Z"),  # за пределами окна из 14 дней
        ("call-30", "2026-10-11T09:00:00Z"),  # вчера
    ],
)
async def test_time_that_is_not_a_slot_returns_slot_not_available(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
    event_type_id: str,
    starts_at: str,
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    response = await post(client, booking(starts_at, event_type_id))

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        "code": "slot_not_available",
        "message": "Время недоступно, выберите другое",
    }
    assert await booking_ids(client) == []


async def test_slot_closer_than_the_notice_is_not_available(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule, notice=120)

    too_early = await post(client, booking("2026-10-12T07:30:00Z"))  # 10:30 при «сейчас» 09:00
    in_time = await post(client, booking("2026-10-12T08:00:00Z"))  # ровно now + 2 часа

    assert too_early.status_code == HTTPStatus.CONFLICT
    assert too_early.json()["code"] == "slot_not_available"
    assert in_time.status_code == HTTPStatus.CREATED


# ───────────────────────── 409 slot_taken ─────────────────────────


async def test_the_same_slot_cannot_be_booked_twice(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking())

    response = await post(client, booking(guest_name="Борис", guest_email="boris@example.com"))

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {"code": "slot_taken", "message": "Слот только что заняли"}
    assert await booking_ids(client) == [NOON]


async def test_booking_of_another_type_blocks_overlapping_time(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking())  # call-30, 12:00–12:30

    response = await post(client, booking("2026-10-12T08:30:00Z", "call-60"))  # 11:30–12:30

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "slot_taken"


async def test_back_to_back_bookings_are_allowed(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking())  # 12:00–12:30

    before = await post(client, booking("2026-10-12T08:30:00Z"))  # 11:30–12:00
    after = await post(client, booking("2026-10-12T09:30:00Z"))  # 12:30–13:00

    assert before.status_code == HTTPStatus.CREATED
    assert after.status_code == HTTPStatus.CREATED


async def test_one_email_can_book_several_slots(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    statuses = [
        (await post(client, booking(starts_at))).status_code
        for starts_at in ("2026-10-12T07:00:00Z", "2026-10-12T07:30:00Z", "2026-10-13T07:00:00Z")
    ]

    assert statuses == [HTTPStatus.CREATED] * 3
    assert len(await booking_ids(client)) == 3  # noqa: PLR2004


async def test_booked_time_disappears_from_the_slots(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking())  # call-30, 12:00–12:30

    short = await client.get("/api/v1/event-types/call-30/slots")
    long = await client.get("/api/v1/event-types/call-60/slots")

    short_starts = [item["starts_at"] for item in short.json()["days"][0]["slots"]]
    long_starts = [item["starts_at"] for item in long.json()["days"][0]["slots"]]
    assert NOON not in short_starts
    assert NOON not in long_starts
    assert "2026-10-12T08:30:00Z" not in long_starts  # 11:30–12:30 пересекается


# ───────────────────────── список встреч ─────────────────────────


async def test_list_is_empty_without_bookings(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/bookings")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"items": []}


async def test_list_is_sorted_by_start_and_mixes_event_types(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking("2026-10-13T07:00:00Z", "call-60"))
    await post(client, booking("2026-10-12T09:00:00Z"))
    await post(client, booking("2026-10-12T07:00:00Z", "call-60"))

    response = await client.get("/api/v1/bookings")

    assert [(item["starts_at"], item["event_type"]["id"]) for item in response.json()["items"]] == [
        ("2026-10-12T07:00:00Z", "call-60"),
        ("2026-10-12T09:00:00Z", "call-30"),
        ("2026-10-13T07:00:00Z", "call-60"),
    ]


async def test_list_contains_only_upcoming_bookings(
    client: httpx.AsyncClient,
    insert_booking: Callable[..., Awaitable[None]],
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)  # «сейчас» 2026-10-12T06:00Z
    await insert_booking("call-30", "2026-10-11T07:00:00+00:00", "2026-10-11T07:30:00+00:00")
    await insert_booking("call-30", "2026-10-12T05:30:00+00:00", "2026-10-12T06:00:00+00:00")
    await insert_booking("call-30", "2026-10-12T06:00:00+00:00", "2026-10-12T06:30:00+00:00")

    assert await booking_ids(client) == [
        "2026-10-12T06:00:00Z"
    ]  # начало ровно «сейчас» ещё предстоит


# ───────────────────────── ограничение БД и гонки ─────────────────────────


async def test_database_rejects_overlapping_bookings_but_allows_back_to_back(
    client: httpx.AsyncClient,
    insert_booking: Callable[..., Awaitable[None]],
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)
    await insert_booking("call-30", "2026-10-12T09:00:00+00:00", "2026-10-12T10:00:00+00:00")

    await insert_booking("call-30", "2026-10-12T10:00:00+00:00", "2026-10-12T10:30:00+00:00")
    await insert_booking("call-30", "2026-10-12T08:30:00+00:00", "2026-10-12T09:00:00+00:00")
    with pytest.raises(IntegrityError, match="bookings_no_overlap"):
        await insert_booking("call-30", "2026-10-12T09:30:00+00:00", "2026-10-12T10:30:00+00:00")


async def test_simultaneous_requests_for_one_slot_create_exactly_one_booking(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    responses = await asyncio.gather(*(post(client, booking()) for _ in range(5)))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [HTTPStatus.CREATED, *[HTTPStatus.CONFLICT] * 4]
    assert {
        response.json()["code"]
        for response in responses
        if response.status_code == HTTPStatus.CONFLICT
    } == {
        "slot_taken",
    }
    assert await booking_ids(client) == [NOON]


async def test_simultaneous_requests_for_overlapping_types_create_one_booking(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
) -> None:
    await prepare(client, freeze_now, configure_schedule)

    responses = await asyncio.gather(
        post(client, booking("2026-10-12T09:00:00Z", "call-30")),  # 12:00–12:30
        post(client, booking("2026-10-12T08:30:00Z", "call-60")),  # 11:30–12:30
    )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [HTTPStatus.CREATED, HTTPStatus.CONFLICT]
    assert len(await booking_ids(client)) == 1


async def test_database_constraint_alone_reports_slot_taken(
    client: httpx.AsyncClient,
    freeze_now: Callable[[str], None],
    configure_schedule: Callable[..., None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await prepare(client, freeze_now, configure_schedule)
    await post(client, booking())

    async def never_overlaps(*_: object) -> bool:
        return False

    # Без быстрой предпроверки пересечение ловит только ограничение БД — как при гонке запросов.
    monkeypatch.setattr(bookings, "_overlaps_existing_booking", never_overlaps)
    response = await post(client, booking(guest_email="boris@example.com"))

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "slot_taken"
    assert await booking_ids(client) == [NOON]
