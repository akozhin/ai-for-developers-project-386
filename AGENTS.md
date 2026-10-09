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
| **Тесты** | `make test` (`make test-backend`, `make test-frontend`) |
| **Линтер** | `make lint` (ruff + ESLint + Prettier + tsp format) |
| Типы | `make typecheck` (mypy + tsc) |
| Автоисправление | `make format` |
| Сборка frontend | `make build` |
| **Генерация из контракта** | `make generate` (TypeSpec → `api/openapi.yaml`; позже и SDK frontend); `make generate-check` падает, если результат не закоммичен |
| Полный прогон как в CI | `make ci` |

Один тест:

- backend: `cd backend && uv run pytest tests/test_health.py::test_health_returns_ok`
- frontend: `cd frontend && pnpm vitest run tests/home.test.tsx` (или `-t "<имя>"`)

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

- **Бизнес-логика только в backend** (расчёт слотов, бронирование); frontend — тонкий UI поверх REST `/api/v1/...`, `/health` — без версии. Контракт — Design First: **любое изменение API начинается с TypeSpec** (`api/`), затем `make generate`, затем код; сгенерированные файлы руками не правятся ([ADR-002](docs/decisions/002-api-contract-typespec.md)). `docs/concept/api-contracts.md` — устаревающий черновик (реализуется в sprint-02, пока есть только `/health`).
- Backend: `app/main.py` собирает приложение через `create_app()`, роутеры в `app/routers/` (1 роутер = 1 файл), настройки — `app/config.py` (pydantic-settings, fail-fast). БД, Alembic и модели пока не созданы (YAGNI до sprint-02), `make migrate*` — заглушки.
- Двойное бронирование исключается ограничением в БД (`UNIQUE` по слоту); время хранится в UTC (`TIMESTAMPTZ`). См. `docs/concept/data-model.md`.
- Тесты backend: `asyncio_mode=auto`, приложение тестируется через `httpx.ASGITransport` без поднятия сервера.

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

Single-context: `GLOSSARY.md` в корне (когда появится), ADR — в `docs/decisions/`. См. `docs/agents/domain.md`.
