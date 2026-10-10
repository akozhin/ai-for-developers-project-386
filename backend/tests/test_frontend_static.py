"""Собранный frontend (статический экспорт Next.js) отдаётся тем же процессом, что и API."""

from collections.abc import AsyncIterator
from http import HTTPStatus
from pathlib import Path

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    """Каталог в формате `next build` с `output: export`."""
    root = tmp_path / "out"
    (root / "_next" / "static").mkdir(parents=True)
    (root / "admin").mkdir()
    (root / "index.html").write_text("<html>главный экран</html>", encoding="utf-8")
    (root / "admin.html").write_text("<html>кабинет</html>", encoding="utf-8")
    (root / "admin" / "index.txt").write_text("служебные данные Next.js", encoding="utf-8")
    (root / "404.html").write_text("<html>нет такой страницы</html>", encoding="utf-8")
    (root / "_next" / "static" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("секрет", encoding="utf-8")
    return root


@pytest.fixture
async def site(dist: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    transport = httpx.ASGITransport(app=create_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_root_serves_the_main_page(site: httpx.AsyncClient) -> None:
    response = await site.get("/")

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"].startswith("text/html")
    assert "главный экран" in response.text


async def test_admin_path_serves_admin_html_not_the_directory(site: httpx.AsyncClient) -> None:
    response = await site.get("/admin")

    assert response.status_code == HTTPStatus.OK
    assert "кабинет" in response.text


async def test_static_assets_are_served_and_cached(site: httpx.AsyncClient) -> None:
    response = await site.get("/_next/static/app.js")

    assert response.status_code == HTTPStatus.OK
    assert response.text == "console.log(1)"
    assert "immutable" in response.headers["cache-control"]


async def test_unknown_page_returns_the_404_page(site: httpx.AsyncClient) -> None:
    response = await site.get("/нет-такой-страницы")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "нет такой страницы" in response.text


async def test_unknown_api_path_still_returns_a_json_error(site: httpx.AsyncClient) -> None:
    response = await site.get("/api/v1/нет-такого")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"code": "not_found", "message": "Ресурс не найден"}


async def test_api_and_contract_routes_take_precedence(site: httpx.AsyncClient) -> None:
    health = await site.get("/health")
    contract = await site.get("/openapi.json")

    assert health.json() == {"status": "ok"}
    assert contract.json()["info"]["title"] == "Запись на звонок"


@pytest.mark.parametrize(
    "path", ["/%2e%2e/secret.txt", "/..%2fsecret.txt", "/_next/../../secret.txt"]
)
async def test_paths_outside_the_site_directory_are_not_served(
    site: httpx.AsyncClient,
    path: str,
) -> None:
    response = await site.get(path)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "секрет" not in response.text


async def test_head_request_for_a_page_succeeds(site: httpx.AsyncClient) -> None:
    response = await site.head("/admin")

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"].startswith("text/html")


async def test_null_byte_in_the_path_is_a_plain_not_found(site: httpx.AsyncClient) -> None:
    response = await site.get("/%00")

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_symlink_pointing_outside_the_site_is_not_followed(
    site: httpx.AsyncClient,
    dist: Path,
) -> None:
    (dist / "leak.txt").symlink_to(dist.parent / "secret.txt")

    response = await site.get("/leak.txt")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "секрет" not in response.text


async def test_without_a_404_page_unknown_path_returns_the_json_error(
    dist: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (dist / "404.html").unlink()
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    transport = httpx.ASGITransport(app=create_app(), raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/нет-такой-страницы")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"code": "not_found", "message": "Ресурс не найден"}
