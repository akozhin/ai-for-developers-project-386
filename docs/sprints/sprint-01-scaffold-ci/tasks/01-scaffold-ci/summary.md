# Summary: Task 01 — Каркас, тесты, линтеры, CI и release-please

> **План:** [plan.md](./plan.md)
> **PR:** [#1 feat: project scaffold with CI](https://github.com/akozhin/ai-for-developers-project-386/pull/1), release-PR: [#2](https://github.com/akozhin/ai-for-developers-project-386/pull/2)
> **Дата закрытия:** 2026-10-07

---

## Что реализовано

- `backend/` — FastAPI (`create_app()`, `GET /health`), pydantic-settings, дымовой тест `tests/test_health.py`, ruff `ALL`, mypy strict
- `frontend/` — Next.js 16 + Tailwind 4 + shadcn/ui, дымовой тест `tests/home.test.tsx` (Vitest), ESLint + Prettier, `tsc`
- `Makefile` (с `make help`), `docker-compose.yml` (PostgreSQL), `.env.example`
- `.github/workflows/ci.yml` — линтеры, типы, тесты, сборка на каждый push и PR
- `.github/workflows/release-please.yml`, `release-please-config.json`, `.release-please-manifest.json`
- `AGENTS.md` в корне: команды, тесты, линтер, правило про Conventional Commits
- `README.md` — как запустить и как проверить требования задания; `docs/` — концепт, ADR-001, roadmap, sprint-01

---

## Отклонения от плана

- Включена настройка репозитория «Allow GitHub Actions to create and approve pull requests» (через `gh api`) — без неё release-please не создаёт PR.
- Токену `gh` добавлено право `workflow` (иначе GitHub отклонял push файлов в `.github/workflows/`).
- Методология (`.methodology/`, `.cursor/`) по просьбе пользователя в git не коммитится; `CLAUDE.md` заменён универсальным `AGENTS.md`.
- Версия `@types/node` приведена к `^24` (совпадает с Node 24 в CI).

---

## Принятые решения

| Решение | Причина | Ссылка на ADR |
|---------|---------|--------------|
| Монорепо, одна версия на оба компонента | Один репозиторий Hexlet, один релизный поток | [ADR-001](../../../decisions/001-tech-stack.md) |
| Команды только через `make`, CI вызывает те же цели | Локальный и CI-прогон идентичны | ADR-001 |
| Squash merge с заголовком `feat: ...` | release-please считает версию по заголовку | ADR-001 |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `shadcn init` записал `--font-sans: var(--font-sans)` (цикл), шрифт не применялся | Исправлено на `var(--font-geist-sans)` |
| CI frontend падал: `Cannot find name 'LayoutProps'` — тип генерирует Next, в чистом checkout его нет | `type-check` = `next typegen && tsc --noEmit` |
| Push отклонён: нет права `workflow` | `gh auth refresh -s workflow` (пользователь), push через credential helper `gh` |
| Release-PR получил версию 1.0.0, а не 0.1.0 | Первый `feat` при стартовой версии 0.0.0 даёт major; при необходимости — `bump-minor-pre-major`/`release-as` в конфиге |
| CI на ветке release-PR: `action_required` | GitHub требует ручного подтверждения workflows для PR от бота; на задание не влияет |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `/health` отвечает 200 | ✅ `{"status":"ok"}` |
| 2 | Frontend собирается и открывается | ✅ `make build`, страница «Запись на звонок» |
| 3 | Тесты проходят | ✅ pytest 1/1, Vitest 1/1 |
| 4 | Lint и типы проходят | ✅ `make ci` = 0 |
| 5 | CI зелёный на push | ✅ PR #1: Backend, Frontend, hexlet-check |
| 6 | release-PR после мержа | ✅ PR #2 `chore(main): release 1.0.0` |

---

## Версии (на 2026-10-07)

| Компонент | Версия |
|-----------|--------|
| Python / uv | 3.12 / 0.10 |
| FastAPI, uvicorn, SQLAlchemy, Alembic, asyncpg, Pydantic | 0.142, 0.54, 2.1, 1.20, 0.32, 2.13 |
| pytest, pytest-asyncio, httpx, ruff, mypy | 9.1, 1.4, 0.28, 0.16, 2.4 |
| Node (CI) / pnpm | 24 / 10.33 |
| Next.js, React, Tailwind, TypeScript | 16.4, 19.3, 4.3, 5.9 |
| ESLint, Prettier, Vitest | 9, 3.9, 5.0 |
| GitHub Actions | checkout@v4, setup-uv@v5, pnpm/action-setup@v4, setup-node@v4, release-please-action@v4 |

---

## Что дальше

Sprint 02 «Ядро бронирования»: PostgreSQL, Alembic, API типов звонков, слотов и записей.
