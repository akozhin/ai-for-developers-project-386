# AGENTS.md

Проект «Запись на звонок»: монорепо `backend/` (FastAPI, uv) + `frontend/` (Next.js, pnpm). Все команды — из корня через `make`.

## Команды

| Что | Команда |
|-----|---------|
| Список всех команд | `make help` |
| Установить зависимости | `make install` |
| Запустить backend (http://localhost:8000) | `make dev-backend` |
| Запустить frontend (http://localhost:3000) | `make dev-frontend` |
| Запустить всё | `make dev` |
| **Тесты** | `make test` (`make test-backend`, `make test-frontend`) |
| **Линтер** | `make lint` (ruff + ESLint + Prettier) |
| Типы | `make typecheck` (mypy + tsc) |
| Сборка frontend | `make build` |
| Полный прогон как в CI | `make ci` |

## Формат коммитов

Только [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <описание в повелительном наклонении, строчными, без точки>`.

- `type`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`
- `scope`: `backend`, `frontend`, `infra`, `program`
- Примеры: `feat(backend): add slots endpoint`, `fix(frontend): handle empty slot list`
- Breaking change — `feat!:` или футер `BREAKING CHANGE:`.
- В `main` — только через PR со squash merge; заголовок PR тоже в формате Conventional Commits (по нему release-please считает версию).

## Прочее

- Не менять `.github/workflows/hexlet-check.yml`.
- Секреты — только в `.env` (не коммитится), образец — `.env.example`.
- Frontend на Next.js 16: перед правками читать `frontend/AGENTS.md`.
- Документация — в `docs/` ([навигатор](docs/README.md)).
