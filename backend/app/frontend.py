"""Раздача собранного frontend (статический экспорт Next.js) тем же процессом, что и API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from starlette.exceptions import HTTPException

IMMUTABLE_PREFIX = "_next/static/"
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


def _find_file(root: Path, path: str) -> Path | None:
    """Файл для пути: сам файл, `<путь>.html` (страницы Next.js) или `<путь>/index.html`."""
    for candidate in (root / path, root / f"{path}.html", root / path / "index.html"):
        try:
            resolved = candidate.resolve()
        except ValueError:  # недопустимый символ в пути, например нулевой байт
            return None
        if resolved.is_relative_to(root) and resolved.is_file():
            return resolved
    return None


def mount_frontend(application: FastAPI, dist: Path) -> None:
    """Добавить в конец маршрутов раздачу страниц и ассетов из `dist`.

    Регистрируется после API-маршрутов: `/health`, `/docs` и `/api/v1/...` имеют приоритет,
    неизвестные пути API по-прежнему отвечают JSON-ошибкой, остальные — страницей 404.
    """
    root = dist.resolve()

    @application.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_frontend(path: str) -> Response:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404)
        found = _find_file(root, path.rstrip("/") or "index")
        if found is None:
            not_found_page = root / "404.html"
            if not_found_page.is_file():
                return FileResponse(not_found_page, status_code=404)
            raise HTTPException(status_code=404)
        headers = {"Cache-Control": IMMUTABLE_CACHE} if path.startswith(IMMUTABLE_PREFIX) else None
        return FileResponse(found, headers=headers)
