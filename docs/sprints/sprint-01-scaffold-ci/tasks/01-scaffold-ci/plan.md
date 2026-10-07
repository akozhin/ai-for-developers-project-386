# Task 01: Каркас, тесты, линтеры, CI и release-please

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** chore
> **Ветка:** `chore/infra-1-scaffold`
> **Spec:** без spec

---

## Цель

Работающий каркас backend (FastAPI) и frontend (Next.js) с дымовыми тестами, линтерами, CI на GitHub Actions и release-please.

---

## Состав работ

- [x] Выбрать стек, зафиксировать в [ADR-001](../../../../decisions/001-tech-stack.md)
- [x] Каркас backend (uv, FastAPI, `/health`)
- [x] Каркас frontend (Next.js, Tailwind 4, shadcn/ui), страница открывается и собирается
- [x] Тестовые раннеры и по одному дымовому тесту: pytest, Vitest
- [x] Линтеры: ruff (`ALL`), mypy strict, ESLint + Prettier, `tsc`
- [x] `Makefile` как единая точка входа
- [ ] GitHub Actions: тесты и линтеры на каждый push — зелёный прогон
- [ ] release-please отдельным workflow — release-PR после мержа в `main`
- [ ] Самопроверка по DoD
- [ ] (после «ок» пользователя) `summary.md`, обновить sprint README и roadmap

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `/health` отвечает 200 | `make dev-backend`, `curl localhost:8000/health` |
| 2 | Frontend собирается и открывается | `make build`; `make dev-frontend` |
| 3 | Тесты проходят | `make test` |
| 4 | Lint и типы проходят | `make lint typecheck` |
| 5 | CI зелёный на push | `gh run list --branch chore/infra-1-scaffold` |
| 6 | release-PR появился после мержа | `gh pr list --search "release-please"` |

### Пользователь проверяет вручную

Расписка по требованиям задания (команды — в [README](../../../../../README.md#как-проверить-требования-задания)):

- [ ] Backend и frontend запускаются локально
- [ ] Есть команды тестов и линтера (`make test`, `make lint`)
- [ ] Actions на каждый push, прогон зелёный
- [ ] Коммиты по Conventional Commits, после мержа в `main` появился release-PR
- [ ] В корне есть `AGENTS.md` с командами и правилом про формат коммитов

---

## Артефакты

- `backend/` — FastAPI-каркас, `pyproject.toml`, `tests/test_health.py`
- `frontend/` — Next.js-каркас, `tests/home.test.tsx`, конфиги ESLint/Prettier/Vitest
- `Makefile`, `docker-compose.yml`, `.env.example`, `.gitignore`
- `.github/workflows/ci.yml`, `.github/workflows/release-please.yml`
- `release-please-config.json`, `.release-please-manifest.json`
- `AGENTS.md`, `docs/` (методология `.methodology/` — локально, в git не коммитится)

---

## Scope

**Трогаем:** только файлы из списка «Артефакты» и `README.md` (раздел «Стек/Установка/Использование»).

**НЕ трогаем:**
- `.github/workflows/hexlet-check.yml` (требование Hexlet)
- Доменную логику: модели, миграции, API бронирования (sprint-02)

---

## Риски и допущения

- Release-please требует в настройках репозитория: Actions → «Allow GitHub Actions to create and approve pull requests».
- Release-PR создаётся только при `feat`/`fix` коммите в `main`; squash-заголовок PR — `feat: project scaffold with CI`.
- Сеть до github.com нестабильна — возможны повторы запросов.

---

## Открытые вопросы

- [ ] Нужен ли отдельный деплой (не в scope этой задачи)?
