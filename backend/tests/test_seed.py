"""Начальные данные: типы событий на 30 и 60 минут создаются обычными запросами API."""

import httpx
import pytest

from app.seed import SeedError, load_event_types, main, seed_event_types


async def test_seed_creates_the_two_default_event_types(client: httpx.AsyncClient) -> None:
    report = await seed_event_types(client, load_event_types())
    listed = await client.get("/api/v1/event-types")

    assert (report.created, report.existing) == (2, 0)
    assert [
        (item["id"], item["title"], item["duration_minutes"]) for item in listed.json()["items"]
    ] == [
        ("call-30", "Звонок 30 минут", 30),
        ("call-60", "Звонок 60 минут", 60),
    ]


async def test_repeated_seed_is_a_success_and_creates_nothing_new(
    client: httpx.AsyncClient,
) -> None:
    await seed_event_types(client, load_event_types())

    report = await seed_event_types(client, load_event_types())
    listed = await client.get("/api/v1/event-types")

    assert (report.created, report.existing) == (0, 2)
    assert [item["id"] for item in listed.json()["items"]] == ["call-30", "call-60"]


async def test_seed_fails_on_an_error_other_than_a_duplicate(client: httpx.AsyncClient) -> None:
    broken = [
        {"id": "call-1", "title": "Мало", "description": "Слишком коротко", "duration_minutes": 1}
    ]

    with pytest.raises(SeedError, match=r"call-1.*422"):
        await seed_event_types(client, broken)


def test_command_exits_with_error_when_api_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("API_URL", "http://127.0.0.1:9")

    exit_code = main()

    assert exit_code == 1
    assert "Не удалось создать начальные данные" in capsys.readouterr().err
