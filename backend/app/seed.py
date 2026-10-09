"""Начальные данные: отправляет типы событий из `seed/event-types.json` обычными запросами API.

Запуск: `make seed` (адрес API — переменная `API_URL`, по умолчанию http://localhost:8000).
Уже существующий id (`409`) считается успехом, любая другая ошибка — ненулевой код возврата.
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any

import httpx

DEFAULT_SEED_FILE = Path(__file__).resolve().parents[2] / "seed" / "event-types.json"
DEFAULT_API_URL = "http://localhost:8000"


class SeedError(Exception):
    """Запрос на создание начальных данных завершился ошибкой, отличной от дубликата."""


@dataclass(frozen=True)
class SeedReport:
    """Итог: сколько типов создано и сколько уже существовало."""

    created: int
    existing: int


def load_event_types(path: Path = DEFAULT_SEED_FILE) -> list[dict[str, Any]]:
    """Прочитать типы событий из файла начальных данных."""
    items: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return items


async def seed_event_types(client: httpx.AsyncClient, items: list[dict[str, Any]]) -> SeedReport:
    """Создать типы событий через `POST /api/v1/event-types`."""
    created = existing = 0
    for item in items:
        response = await client.post("/api/v1/event-types", json=item)
        if response.status_code == HTTPStatus.CREATED:
            created += 1
        elif response.status_code == HTTPStatus.CONFLICT:
            existing += 1
        else:
            message = f"{item.get('id', '?')}: ответ {response.status_code} {response.text}"
            raise SeedError(message)
    return SeedReport(created=created, existing=existing)


async def _run(api_url: str, items: list[dict[str, Any]]) -> SeedReport:
    async with httpx.AsyncClient(base_url=api_url) as client:
        return await seed_event_types(client, items)


def main() -> int:
    """Точка входа `python -m app.seed`; возвращает код возврата процесса."""
    api_url = os.environ.get("API_URL", DEFAULT_API_URL)
    try:
        report = asyncio.run(_run(api_url, load_event_types()))
    except (SeedError, httpx.HTTPError, OSError, json.JSONDecodeError) as error:
        sys.stderr.write(f"Не удалось создать начальные данные: {error}\n")
        return 1
    sys.stdout.write(f"Типы событий: создано {report.created}, уже были {report.existing}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
