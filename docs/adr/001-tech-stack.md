# ADR-001: Технологический стек и организация репозитория

> **Статус:** Принято · **Дата:** 2026-10-07

## Контекст

Нужно быстро получить воспроизводимый каркас для учебного проекта с проверкой в CI и автоматизацией релизов. Стек задан требованиями проекта и соглашениями методологии AI-Driven Development (хранится локально).

## Решение

- **Монорепо** `backend/` + `frontend/`: один репозиторий Hexlet, единый CI и один релизный поток.
- **Backend:** Python 3.12, uv, FastAPI + uvicorn, SQLAlchemy 2 async, Alembic, asyncpg, Pydantic v2; ruff (`select = ["ALL"]`), mypy strict, pytest + pytest-asyncio + httpx.
- **Frontend:** Next.js (App Router) + React, TypeScript strict, Tailwind 4, shadcn/ui, pnpm, ESLint + Prettier, **Vitest** + Testing Library.
- **БД:** PostgreSQL, PK — `UUID` (исключение: у типа события PK — slug, который задаёт владелец; см. тикет «Сущности и схемы контракта»).
- **Команды:** только через `make`; CI вызывает те же цели.
- **Релизы:** release-please (`release-type: simple`, одна версия на монорепо), Conventional Commits, squash merge.
- Файл `.github/workflows/hexlet-check.yml` не изменяется (требование Hexlet).

## Последствия

- (+) Один набор команд локально и в CI.
- (+) Release-PR формируется автоматически.
- (−) Единая версия для backend и frontend — достаточно для учебного проекта.
- (−) Next.js 16 отличается от привычных версий — перед правками читаем `frontend/AGENTS.md`.
