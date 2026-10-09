"""Типы событий: создание, список, чтение по id (контракт: /api/v1/event-types)."""

from http import HTTPStatus

import httpx
import pytest

CALL_30 = {
    "id": "call-30",
    "title": "Звонок 30 минут",
    "description": "Короткий созвон: знакомство или быстрый вопрос",
    "duration_minutes": 30,
}


async def test_list_is_empty_when_nothing_created(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/event-types")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"items": []}


async def test_created_event_type_is_returned_in_list(client: httpx.AsyncClient) -> None:
    created = await client.post("/api/v1/event-types", json=CALL_30)
    listed = await client.get("/api/v1/event-types")

    assert created.status_code == HTTPStatus.CREATED
    assert created.json() == CALL_30
    assert listed.status_code == HTTPStatus.OK
    assert listed.json() == {"items": [CALL_30]}


async def test_event_type_is_returned_by_id(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)

    response = await client.get("/api/v1/event-types/call-30")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == CALL_30


async def test_unknown_id_returns_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/event-types/call-45")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "code": "event_type_not_found",
        "message": "Тип события не найден",
    }


async def test_malformed_id_in_path_also_returns_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/event-types/Не_slug!")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "event_type_not_found"


async def test_duplicate_id_returns_conflict_and_keeps_the_original(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/api/v1/event-types", json=CALL_30)

    response = await client.post(
        "/api/v1/event-types",
        json={**CALL_30, "title": "Другое название", "duration_minutes": 45},
    )
    stored = await client.get("/api/v1/event-types/call-30")

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        "code": "event_type_exists",
        "message": "Тип события с таким id уже существует",
    }
    assert stored.json() == CALL_30


async def test_list_is_sorted_by_duration(client: httpx.AsyncClient) -> None:
    call_60 = {**CALL_30, "id": "call-60", "title": "Звонок 60 минут", "duration_minutes": 60}
    await client.post("/api/v1/event-types", json=call_60)
    await client.post("/api/v1/event-types", json=CALL_30)

    response = await client.get("/api/v1/event-types")

    assert [item["id"] for item in response.json()["items"]] == ["call-30", "call-60"]


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"id": "Call_30"}, "id"),
        ({"id": "-call"}, "id"),
        ({"id": "a" * 65}, "id"),
        ({"title": ""}, "title"),
        ({"title": "т" * 101}, "title"),
        ({"description": ""}, "description"),
        ({"description": "о" * 501}, "description"),
        ({"duration_minutes": 4}, "duration_minutes"),
        ({"duration_minutes": 481}, "duration_minutes"),
        ({"duration_minutes": "полчаса"}, "duration_minutes"),
        ({"unexpected": "лишнее"}, "unexpected"),
    ],
)
async def test_invalid_fields_return_validation_error(
    client: httpx.AsyncClient,
    changes: dict[str, object],
    field: str,
) -> None:
    response = await client.post("/api/v1/event-types", json={**CALL_30, **changes})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "validation_error"
    assert field in [item["field"] for item in response.json()["fields"]]


@pytest.mark.parametrize("missing", ["id", "title", "description", "duration_minutes"])
async def test_missing_field_returns_validation_error(
    client: httpx.AsyncClient,
    missing: str,
) -> None:
    payload = {key: value for key, value in CALL_30.items() if key != missing}

    response = await client.post("/api/v1/event-types", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [item["field"] for item in response.json()["fields"]] == [missing]


@pytest.mark.parametrize("duration", [5, 480])
async def test_duration_boundaries_are_accepted(client: httpx.AsyncClient, duration: int) -> None:
    response = await client.post(
        "/api/v1/event-types",
        json={**CALL_30, "duration_minutes": duration},
    )

    assert response.status_code == HTTPStatus.CREATED


async def test_equal_durations_are_ordered_by_id(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/event-types", json={**CALL_30, "id": "b-talk"})
    await client.post("/api/v1/event-types", json={**CALL_30, "id": "a-talk"})

    response = await client.get("/api/v1/event-types")

    assert [item["id"] for item in response.json()["items"]] == ["a-talk", "b-talk"]
