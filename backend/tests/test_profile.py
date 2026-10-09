"""Профиль владельца для шапки главного экрана: имя, часовой пояс, аватар, доступность AI."""

from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path

import httpx
import pytest

from app.config import Settings


async def test_default_profile_has_default_name_avatar_and_no_ai(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/profile")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "name": "Alexandr Kozhin",
        "timezone": "Europe/Moscow",
        "avatar_url": "/avatar.jpg",
        "ai_enabled": False,
    }


async def test_profile_follows_configuration(
    client: httpx.AsyncClient,
    configure_settings: Callable[..., None],
) -> None:
    configure_settings(
        owner_name="Анна Иванова",
        owner_timezone="Asia/Yekaterinburg",
        owner_avatar_url="https://cdn.example.com/anna.png",
    )

    response = await client.get("/api/v1/profile")

    assert response.json() == {
        "name": "Анна Иванова",
        "timezone": "Asia/Yekaterinburg",
        "avatar_url": "https://cdn.example.com/anna.png",
        "ai_enabled": False,
    }


async def test_profile_without_avatar_returns_null(
    client: httpx.AsyncClient,
    configure_settings: Callable[..., None],
) -> None:
    configure_settings(owner_avatar_url=None)

    response = await client.get("/api/v1/profile")

    assert response.json()["avatar_url"] is None


@pytest.mark.parametrize(("key", "enabled"), [("sk-test-123", True), ("", False), ("   ", False)])
async def test_ai_is_enabled_only_with_a_non_empty_key_and_never_leaks_it(
    client: httpx.AsyncClient,
    configure_settings: Callable[..., None],
    key: str,
    enabled: bool,  # noqa: FBT001
) -> None:
    configure_settings(ai_api_key=key)

    response = await client.get("/api/v1/profile")

    assert response.json()["ai_enabled"] is enabled
    assert "sk-test-123" not in response.text


def test_blank_avatar_and_key_in_environment_mean_not_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)  # нет файла .env
    monkeypatch.setenv("OWNER_AVATAR_URL", "")
    monkeypatch.setenv("AI_API_KEY", "")

    settings = Settings()

    assert settings.owner_avatar_url is None
    assert settings.ai_enabled is False
