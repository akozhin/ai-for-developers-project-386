"""AI-подбор слотов: `POST /api/v1/slot-suggestions` с заглушкой модели вместо реальной."""

from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app import slot_agent
from app.dependencies import get_chat_model_factory
from app.slot_search import MAX_FOUND_SLOTS
from tests.ai_stub import Reply, ScriptedChatModel, call_search, final_answer, model_factory

URL = "/api/v1/slot-suggestions"
CALL_30 = {
    "id": "call-30",
    "title": "Звонок 30 минут",
    "description": "Короткий созвон",
    "duration_minutes": 30,
}
# Понедельник 2026-10-12, 09:00 по Москве; с запасом 2 часа первый слот — 11:00 MSK (08:00Z).
NOW = "2026-10-12T06:00:00+00:00"
UseModel = Callable[..., ScriptedChatModel]
NO_SLOTS_TEXT = "Не нашлось подходящих слотов, попробуйте другое время"


@pytest.fixture(autouse=True)
def _frozen_now(freeze_now: Callable[[str], None]) -> None:
    freeze_now(NOW)


@pytest.fixture
async def event_type(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/event-types", json=CALL_30)
    assert response.status_code == HTTPStatus.CREATED


@pytest.fixture
def ai_on(configure_settings: Callable[..., None]) -> None:
    configure_settings(ai_api_key="test-key")


@pytest.fixture
def use_model(
    app: FastAPI,
    ai_on: None,  # noqa: ARG001
) -> UseModel:
    def use(script: list[Reply], delay_seconds: float = 0) -> ScriptedChatModel:
        model = ScriptedChatModel(script=script, delay_seconds=delay_seconds)
        app.dependency_overrides[get_chat_model_factory] = model_factory(model)
        return model

    return use


async def suggest(
    client: httpx.AsyncClient,
    text: str = "что-нибудь на этой неделе",
    timezone: str = "Europe/Moscow",
    event_type_id: str = "call-30",
) -> httpx.Response:
    body = {"event_type_id": event_type_id, "text": text, "timezone": timezone}
    return await client.post(URL, json=body)


def starts(model: ScriptedChatModel, call: int = 0) -> list[str]:
    return [item["starts_at"] for item in model.tool_results()[call]["slots"]]


@pytest.mark.usefixtures("event_type")
async def test_without_api_key_returns_ai_unavailable(
    client: httpx.AsyncClient,
    configure_settings: Callable[..., None],
) -> None:
    configure_settings(ai_api_key=None)
    response = await suggest(client)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["code"] == "ai_unavailable"


@pytest.mark.usefixtures("event_type")
async def test_suggestion_has_text_and_slots_with_first_recommended(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model(
        [
            call_search(date_from="2026-10-12", date_to="2026-10-12"),
            final_answer(
                "Нашёл два варианта",
                "2026-10-12T08:00:00Z",
                "2026-10-12T08:30:00Z",
            ),
        ],
    )

    response = await suggest(client)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "text": "Нашёл два варианта",
        "items": [
            {
                "starts_at": "2026-10-12T08:00:00Z",
                "ends_at": "2026-10-12T08:30:00Z",
                "recommended": True,
            },
            {
                "starts_at": "2026-10-12T08:30:00Z",
                "ends_at": "2026-10-12T09:00:00Z",
                "recommended": False,
            },
        ],
    }


@pytest.mark.usefixtures("event_type")
async def test_at_most_three_slots_are_returned(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model(
        [
            final_answer(
                "Много вариантов",
                *(f"2026-10-12T{hour}:00:00Z" for hour in ("08", "09", "10", "11", "12")),
            ),
        ],
    )

    items = (await suggest(client)).json()["items"]

    assert [item["starts_at"] for item in items] == [
        "2026-10-12T08:00:00Z",
        "2026-10-12T09:00:00Z",
        "2026-10-12T10:00:00Z",
    ]
    assert [item["recommended"] for item in items] == [True, False, False]


@pytest.mark.usefixtures("event_type")
async def test_search_by_date_range_returns_only_that_range(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    model = use_model(
        [
            call_search(date_from="2026-10-13", date_to="2026-10-14", time_from="17:00"),
            final_answer("Готово"),
        ],
    )

    await suggest(client)

    assert starts(model) == [
        "2026-10-13T17:00:00+03:00",
        "2026-10-13T17:30:00+03:00",
        "2026-10-14T17:00:00+03:00",
        "2026-10-14T17:30:00+03:00",
    ]


@pytest.mark.usefixtures("event_type")
async def test_search_by_weekdays_returns_only_those_days(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    model = use_model(
        [
            call_search(date_from="2026-10-12", date_to="2026-10-18", weekdays=["wed", "fri"]),
            final_answer("Готово"),
        ],
    )

    await suggest(client)

    days = {value[:10] for value in starts(model)}
    assert days == {"2026-10-14", "2026-10-16"}


@pytest.mark.usefixtures("event_type")
async def test_search_by_time_interval_uses_guest_timezone(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    # Гость в Екатеринбурге (UTC+5): 12:00–14:00 у него — 10:00–12:00 по Москве.
    model = use_model(
        [
            call_search(
                date_from="2026-10-13", date_to="2026-10-13", time_from="12:00", time_to="14:00"
            ),
            final_answer("Готово"),
        ],
    )

    await suggest(client, timezone="Asia/Yekaterinburg")

    assert starts(model) == [
        "2026-10-13T12:00:00+05:00",
        "2026-10-13T12:30:00+05:00",
        "2026-10-13T13:00:00+05:00",
        "2026-10-13T13:30:00+05:00",
    ]


@pytest.mark.usefixtures("event_type")
async def test_weekday_and_dates_are_taken_in_guest_timezone(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    # Рабочий день владельца кончается в 18:00 MSK, во Владивостоке (UTC+10) это уже 01:00.
    model = use_model(
        [
            call_search(
                date_from="2026-10-14", date_to="2026-10-14", time_from="00:00", time_to="02:00"
            ),
            final_answer("Готово"),
        ],
    )

    await suggest(client, timezone="Asia/Vladivostok")

    assert starts(model) == [
        "2026-10-14T00:00:00+10:00",
        "2026-10-14T00:30:00+10:00",
    ]


@pytest.mark.usefixtures("event_type")
async def test_one_search_returns_at_most_twenty_slots_in_ascending_order(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    model = use_model([call_search(limit=100), final_answer("Готово")])

    await suggest(client)

    found = starts(model)
    assert len(found) == MAX_FOUND_SLOTS
    assert found == sorted(found)
    assert found[0] == "2026-10-12T11:00:00+03:00"


@pytest.mark.usefixtures("event_type")
async def test_booked_time_is_not_found(
    client: httpx.AsyncClient,
    use_model: UseModel,
    insert_booking: Callable[..., Awaitable[None]],
) -> None:
    await insert_booking("call-30", "2026-10-12T08:00:00+00:00", "2026-10-12T08:30:00+00:00")
    model = use_model(
        [
            call_search(date_from="2026-10-12", date_to="2026-10-12", limit=2),
            final_answer("Готово"),
        ],
    )

    await suggest(client)

    assert starts(model) == ["2026-10-12T11:30:00+03:00", "2026-10-12T12:00:00+03:00"]


@pytest.mark.usefixtures("event_type")
async def test_invented_slots_are_dropped(
    client: httpx.AsyncClient,
    use_model: UseModel,
    insert_booking: Callable[..., Awaitable[None]],
) -> None:
    await insert_booking("call-30", "2026-10-12T09:00:00+00:00", "2026-10-12T09:30:00+00:00")
    use_model(
        [
            final_answer(
                "Вот варианты",
                "2026-10-12T09:00:00Z",  # занято
                "2026-10-17T09:00:00Z",  # суббота
                "2026-10-12T09:10:00Z",  # не на сетке
                "2026-10-12T05:00:00Z",  # раньше «сейчас» плюс запас
                "2026-10-12T10:00:00Z",  # настоящий
                "2026-10-12T10:00:00Z",  # дубль
            ),
        ],
    )

    body = (await suggest(client)).json()

    assert [item["starts_at"] for item in body["items"]] == ["2026-10-12T10:00:00Z"]
    assert body["items"][0]["recommended"] is True
    assert body["text"] == "Вот варианты"


@pytest.mark.usefixtures("event_type")
async def test_when_nothing_is_left_items_are_empty_with_fallback_text(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model([final_answer("Отлично, вот слот!", "2026-10-17T09:00:00Z")])

    response = await suggest(client)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"text": NO_SLOTS_TEXT, "items": []}


@pytest.mark.usefixtures("event_type")
async def test_unclear_phrase_returns_model_text_and_no_items(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model([final_answer("Не понял пожелание: уточните день и время")])

    response = await suggest(client, text="asdf qwerty")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"text": "Не понял пожелание: уточните день и время", "items": []}


@pytest.mark.usefixtures("event_type")
async def test_tool_is_called_at_most_three_times(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    model = use_model([*(call_search(limit=1) for _ in range(4)), final_answer("Готово")])

    response = await suggest(client)

    assert response.status_code == HTTPStatus.OK
    results = model.tool_results()
    assert [("slots" in result) for result in results] == [True, True, True, False]


@pytest.mark.usefixtures("event_type")
async def test_model_failure_returns_ai_unavailable(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model([RuntimeError("provider is down")])

    response = await suggest(client)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["code"] == "ai_unavailable"


@pytest.mark.usefixtures("event_type")
async def test_model_timeout_returns_ai_unavailable(
    client: httpx.AsyncClient,
    use_model: UseModel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(slot_agent, "AGENT_TIMEOUT_SECONDS", 0.05)
    use_model([final_answer("Поздно")], delay_seconds=0.5)

    response = await suggest(client)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["code"] == "ai_unavailable"


@pytest.mark.usefixtures("ai_on")
async def test_unknown_event_type_returns_not_found(client: httpx.AsyncClient) -> None:
    response = await suggest(client, event_type_id="call-45")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "event_type_not_found"


@pytest.mark.parametrize(
    ("body_patch", "field"),
    [
        ({"text": ""}, "text"),
        ({"text": "я" * 501}, "text"),
        ({"timezone": "Mars/Base"}, "timezone"),
        ({"timezone": "Europe"}, "timezone"),
        ({"extra": 1}, "extra"),
    ],
)
@pytest.mark.usefixtures("event_type", "ai_on")
async def test_invalid_input_returns_validation_error(
    client: httpx.AsyncClient,
    body_patch: dict[str, Any],
    field: str,
) -> None:
    body = {"event_type_id": "call-30", "text": "завтра", "timezone": "Europe/Moscow", **body_patch}

    response = await client.post(URL, json=body)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [item["field"] for item in response.json()["fields"]] == [field]


@pytest.mark.usefixtures("event_type")
async def test_text_of_exactly_500_characters_is_accepted(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model([final_answer("Ок")])

    response = await suggest(client, text="я" * 500)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("event_type")
async def test_eleventh_request_in_a_minute_is_rate_limited(
    client: httpx.AsyncClient,
    configure_settings: Callable[..., None],
) -> None:
    configure_settings(ai_api_key=None)  # без ключа запросы не доходят до модели
    statuses = [(await suggest(client)).status_code for _ in range(11)]

    assert statuses[:10] == [HTTPStatus.SERVICE_UNAVAILABLE] * 10
    assert statuses[10] == HTTPStatus.TOO_MANY_REQUESTS
    last = await suggest(client)
    assert last.json()["code"] == "rate_limited"


@pytest.mark.usefixtures("event_type")
async def test_blank_model_text_does_not_discard_valid_slots(
    client: httpx.AsyncClient,
    use_model: UseModel,
) -> None:
    use_model([final_answer("  ", "2026-10-12T08:00:00Z")])

    body = (await suggest(client)).json()

    assert [item["starts_at"] for item in body["items"]] == ["2026-10-12T08:00:00Z"]
    assert body["text"]
