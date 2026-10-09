"""`/openapi.json` и `/docs` отдают закоммиченный контракт, а не схему из кода."""

from http import HTTPStatus

import httpx


async def test_openapi_json_is_the_committed_contract(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")

    document = response.json()
    assert response.status_code == HTTPStatus.OK
    assert document["openapi"] == "3.1.0"
    assert document["info"]["title"] == "Запись на звонок"
    # Эти маршруты ещё не реализованы в коде: они могут попасть сюда только из контракта.
    assert "/api/v1/event-types" in document["paths"]
    assert "/api/v1/bookings" in document["paths"]


async def test_docs_page_is_available(client: httpx.AsyncClient) -> None:
    response = await client.get("/docs")

    assert response.status_code == HTTPStatus.OK
    assert "text/html" in response.headers["content-type"]
