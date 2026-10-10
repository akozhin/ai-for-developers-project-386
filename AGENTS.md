# AGENTS.md

«Запись на звонок» — упрощённый Cal.com: владелец публикует слоты, гость записывается (без авторизации и внешних календарей). Тестовое задание Hexlet «AI for Developers». Монорепо: `api/` (контракт TypeSpec, pnpm) + `backend/` (FastAPI, uv) + `frontend/` (Next.js, pnpm). Документация — [docs/README.md](docs/README.md).

## Команды

Все команды — из корня через `make` (`make help` — список). Прямые вызовы `uv`/`pnpm` в доках и CI не используются.

| Что | Команда |
|-----|---------|
| Список всех команд | `make help` |
| Установить зависимости | `make install` |
| Запустить backend (http://localhost:8000) | `make dev-backend` |
| Запустить frontend (http://localhost:3000) | `make dev-frontend` |
| Запустить всё | `make dev` |
| PostgreSQL в Docker / остановить | `make up` / `make down` (нужна для `make test-backend` и `make dev-backend`) |
| Миграции | `make migrate`, `make migrate-new m=<название>` |
| Начальные данные (типы 30 и 60 минут) | `make seed` (нужны запущенные backend и БД; повтор безопасен) |
| **Тесты** | `make test` (`make test-backend`, `make test-frontend`) |
| **Линтер** | `make lint` (ruff + ESLint + Prettier + tsp format) |
| Типы | `make typecheck` (mypy + tsc) |
| Автоисправление | `make format` |
| Сборка frontend | `make build` |
| **Генерация из контракта** | `make generate` (TypeSpec → `api/openapi.yaml` → SDK frontend в `frontend/lib/api/generated`); `make generate-check` падает, если результат не закоммичен |
| Docker-образ | `make docker-build`, `make docker-run` (порт — `PORT`, по умолчанию 8000; ADR-004) |
| Полный прогон как в CI | `make ci` |

Один тест:

- backend: `cd backend && uv run pytest tests/test_health.py::test_health_returns_ok`
- frontend: `cd frontend && pnpm vitest run tests/booking-screen.test.tsx` (или `-t "<имя>"`)

## Формат коммитов

Только [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <описание в повелительном наклонении, строчными, без точки>`.

- `type`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`
- `scope`: `backend`, `frontend`, `infra`, `program`
- Примеры: `feat(backend): add slots endpoint`, `fix(frontend): handle empty slot list`
- Breaking change — `feat!:` или футер `BREAKING CHANGE:`.
- В `main` — только через PR со squash merge; заголовок PR тоже в формате Conventional Commits (по нему release-please считает версию). Release-PR создаётся только при `feat`/`fix`.

## Процесс работы

Работа ведётся по плану задачи `docs/sprints/sprint-NN-*/tasks/NN-*/plan.md`. Два согласования с человеком: план → «ок» → реализация → итог DoD → «ок» → только потом `summary.md` и обновление README спринта и `docs/roadmap.md`. Менять только файлы из раздела «Артефакты» плана.

## Архитектура

- **Бизнес-логика только в backend** (расчёт слотов, бронирование); frontend — тонкий UI поверх REST `/api/v1/...`, `/health` — без версии. Контракт — Design First: **любое изменение API начинается с TypeSpec** (`api/`), затем `make generate`, затем код; сгенерированные файлы руками не правятся ([ADR-002](docs/decisions/002-api-contract-typespec.md)). `docs/concept/api-contracts.md` — краткий обзор контракта (источник правды — `api/main.tsp`).
- Backend: `app/main.py` собирает приложение через `create_app()`, роутеры в `app/routers/` (1 роутер = 1 файл), настройки — `app/config.py` (pydantic-settings, fail-fast). БД — PostgreSQL (`make up`), миграции — Alembic (`make migrate`, `make migrate-new m=<название>`), сессия БД — зависимость `get_session` (`app/db.py`); ошибки API приводятся к формату контракта в `app/errors.py`; `/docs` и `/openapi.json` отдают закоммиченный `api/openapi.yaml`. Модели появляются по мере тикетов.
- Структура backend: `app/slots.py` — расчёт слотов (одна функция для выдачи слотов, проверки бронирования и AI), `app/slot_search.py`/`app/slot_agent.py` — AI-подбор (ADR-003), `app/models.py`, `app/schemas.py`, `app/dependencies.py` (подменяемые в тестах `get_now` и `get_settings`), `app/errors.py` (формат ошибок контракта), `app/seed.py` (`make seed`, данные в `seed/event-types.json`).
- Образ: `Dockerfile` в корне (двухэтапный: статический экспорт frontend → рантайм Python), запуск — `docker/entrypoint.sh` (порт из `PORT`; миграции и начальные данные по `RUN_MIGRATIONS`/`SEED_ON_START`); `app/frontend.py` раздаёт собранный frontend, если каталог `FRONTEND_DIST` существует; `NEXT_OUTPUT=export` включает статический экспорт (`pnpm build:static`), `rewrites` работают только в разработке. Деплой — [ADR-004](docs/decisions/004-docker-render-deploy.md), `render.yaml`.
- Структура frontend: `app/page.tsx` — экран записи (`components/booking/`), `app/admin/` — страница владельца (`components/admin/`); запросы идут через SDK `lib/api/generated` и общий клиент `lib/api/client.ts` на тот же origin, Next.js проксирует `/api/v1/*` на backend (`rewrites`). Типизированные MSW-моки для тестов — в `frontend/mocks/`.
- Двойное бронирование исключается ограничением в БД (`EXCLUDE` по диапазону времени: две встречи, даже разных типов, не пересекаются); время хранится в UTC (`TIMESTAMPTZ`). См. `docs/concept/data-model.md`.
- Тесты backend: `asyncio_mode=auto`, приложение тестируется через `httpx.ASGITransport` без поднятия сервера на реальной PostgreSQL (перед `make test-backend` выполните `make up`; в CI БД — service container); данные очищаются после каждого теста; контракт проверяет Schemathesis (`tests/test_contract.py`).

## Особенности

- **Строгие линтеры:** ruff `select = ["ALL"]` (игноры и `per-file-ignores` — в `backend/pyproject.toml`), mypy strict; в TS запрещены `any` и `@ts-ignore`. Тесты frontend — в `frontend/tests/`, алиас `@/` указывает на корень `frontend/`.
- **Next.js 16** отличается от привычных версий — перед правками читать `frontend/AGENTS.md`.
- shadcn/ui: компоненты в `frontend/components/ui/`, добавлять через `pnpm dlx shadcn@latest add <name>` в `frontend/`; только семантические цвета-токены.
- Не менять `.github/workflows/hexlet-check.yml` и не переименовывать репозиторий (проверки Hexlet).
- Секреты — только в `.env` (не коммитится), образец — `.env.example`.
- Порт 3000 может быть занят Docker; для превью — `.claude/launch.json` (frontend :3100, backend :8000).
- Локальные файлы вне git: `.methodology/`, `.cursor/`, `.claude/` — на них не ссылаться из закоммиченных файлов.

## Agent skills

### Issue tracker

Issues живут в GitHub Issues репозитория (`gh` CLI). См. `docs/agents/issue-tracker.md`.

### Triage labels

Стандартные лейблы: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. См. `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` в корне, ADR — в `docs/decisions/`. См. `docs/agents/domain.md`.
