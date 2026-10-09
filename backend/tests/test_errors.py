"""Единый формат ошибок из контракта: `{code, message}` и `422` со списком полей."""

from http import HTTPStatus

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.errors import ApiError


class Payload(BaseModel):
    """Тело запроса тестового эндпоинта."""

    name: str = Field(min_length=1)
    age: int


async def test_invalid_body_returns_422_with_fields(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    async def echo(payload: Payload) -> Payload:
        return payload

    app.add_api_route("/__echo", echo, methods=["POST"])

    response = await client.post("/__echo", json={"name": "", "age": "много"})

    body = response.json()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert body["code"] == "validation_error"
    assert body["message"] == "Ошибка валидации"
    assert sorted(item["field"] for item in body["fields"]) == ["age", "name"]
    assert all(item["message"] for item in body["fields"])


async def test_missing_body_field_is_reported_by_name(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    async def echo(payload: Payload) -> Payload:
        return payload

    app.add_api_route("/__echo", echo, methods=["POST"])

    response = await client.post("/__echo", json={"name": "Анна"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [item["field"] for item in response.json()["fields"]] == ["age"]


async def test_domain_error_is_rendered_as_code_and_message(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    async def conflict() -> None:
        raise ApiError(HTTPStatus.CONFLICT, "some_conflict", "Конфликт состояния")

    app.add_api_route("/__conflict", conflict)

    response = await client.get("/__conflict")

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {"code": "some_conflict", "message": "Конфликт состояния"}


async def test_unknown_route_returns_not_found_error(client: httpx.AsyncClient) -> None:
    response = await client.get("/нет-такого")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"code": "not_found", "message": "Ресурс не найден"}


async def test_wrong_method_returns_method_not_allowed_error(client: httpx.AsyncClient) -> None:
    response = await client.post("/health")

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.json() == {
        "code": "method_not_allowed",
        "message": "Метод не поддерживается",
    }


async def test_unexpected_exception_returns_internal_error_without_details(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    async def boom() -> None:
        message = "секретные подробности"
        raise RuntimeError(message)

    app.add_api_route("/__boom", boom)

    response = await client.get("/__boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"code": "internal_error", "message": "Внутренняя ошибка"}
    assert "секретные" not in response.text
