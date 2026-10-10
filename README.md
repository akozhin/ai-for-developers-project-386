# Календарь звонков


[![hexlet-check](https://github.com/akozhin/ai-for-developers-project-386/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/akozhin/ai-for-developers-project-386/actions)

Разработайте совместно с ИИ сервис для бронирования календаря

Учебный проект Хекслета: https://ru.hexlet.io/programs/ai-for-developers
Как это должно работать: https://files.hexlet.app/a/2ipc5m

## Как это выглядит

Упрощённый Cal.com: владелец публикует типы событий, гость выбирает свободный слот на ближайшие 14 дней и бронирует его без регистрации. Двойное бронирование исключено — две встречи не пересекаются, даже если это разные типы.

![Экран записи: календарь, слоты и форма подтверждения](docs/mockups/main.png)

А ещё можно просто написать, когда удобно, и AI-агент подберёт подходящие слоты:

![Режим «Подобрать с AI»](docs/mockups/book.png)

> Макеты лежат в [docs/mockups/](docs/mockups/); реализация сделана по [спецификации](https://github.com/akozhin/ai-for-developers-project-386/issues/14). Решения — в [docs/decisions/](docs/decisions/), словарь — в [GLOSSARY.md](GLOSSARY.md), API-контракт — [`api/main.tsp`](api/main.tsp) ([обзор](docs/concept/api-contracts.md)).

## Стек

- **Контракт:** TypeSpec → OpenAPI 3.1 → SDK frontend (`@hey-api/openapi-ts`), Design First
- **Backend:** Python 3.12, uv, FastAPI, SQLAlchemy 2 async, Alembic, PostgreSQL 18, LangChain (AI-подбор слотов)
- **Frontend:** Next.js, React, TypeScript, Tailwind 4, shadcn/ui, pnpm
- **Качество:** ruff, mypy, ESLint, Prettier, pytest, Vitest
- **CI/CD:** GitHub Actions, release-please
- Документация и методология: [docs/](docs/README.md)

## Установка и запуск

Нужны `uv`, `pnpm` (Node 24), `make`, Docker (для PostgreSQL).

```bash
git clone https://github.com/akozhin/ai-for-developers-project-386.git
cd ai-for-developers-project-386
make install        # зависимости backend, frontend и контракта
make up             # PostgreSQL в Docker (порт 5432)
make migrate        # применить миграции
make dev            # backend :8000 и frontend :3000
make seed           # (в другом терминале, при запущенном backend) типы событий на 30 и 60 минут
```

Откройте http://localhost:3000 — экран записи; http://localhost:3000/admin — страница владельца (встречи и типы событий, без авторизации); http://localhost:8000/docs — Swagger UI контракта. `make seed` безопасно повторять: уже существующие типы пропускаются.

Если порт 3000 занят, запустите `make dev-backend` и `PORT=3100 make dev-frontend` по отдельности.

## Команды

```bash
make help           # список всех команд
make test           # тесты backend (pytest, нужна БД: make up) и frontend (Vitest)
make lint           # линтеры: ruff, ESLint, Prettier, tsp format
make typecheck      # mypy и tsc
make generate       # контракт: TypeSpec → api/openapi.yaml → SDK frontend
make generate-check # то же + проверка, что результат закоммичен (есть в CI)
make migrate-new m=<название>  # новая миграция Alembic
make ci             # generate-check + lint + typecheck + test + build, как в CI
```

Полный список команд и правила для агентов — в [AGENTS.md](AGENTS.md).

## Конфигурация

Переменные окружения backend читаются из `backend/.env` (образец — [`backend/.env.example`](backend/.env.example)), frontend — из `frontend/.env.local` ([`frontend/.env.example`](frontend/.env.example)). Значения по умолчанию подходят для локального запуска.

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `DATABASE_URL` | `postgresql+asyncpg://cal:cal@localhost:5432/cal` | Подключение к PostgreSQL |
| `OWNER_TIMEZONE` | `Europe/Moscow` | Часовой пояс владельца (IANA) |
| `WORK_DAYS` | `mon,tue,wed,thu,fri` | Рабочие дни |
| `WORK_START`, `WORK_END` | `10:00`, `18:00` | Рабочие часы, кратны 30 минутам |
| `BOOKING_MIN_NOTICE_MINUTES` | `120` | Не раньше чем через сколько минут можно записаться; `0` — без запаса |
| `OWNER_NAME` | `Alexandr Kozhin` | Имя в профиле |
| `OWNER_AVATAR_URL` | `/avatar.jpg` | Адрес аватара; пусто — инициалы |
| `AI_API_KEY` | — | Ключ AI-провайдера; пусто — AI выключен (`ai_enabled: false`) |
| `AI_BASE_URL`, `AI_MODEL` | OpenRouter, `anthropic/claude-haiku-4.5` | OpenAI-совместимый провайдер и модель (можно локальную) |
| `API_URL` (frontend) | `http://localhost:8000` | Куда Next.js проксирует `/api/v1/*` |

Неверное значение расписания останавливает запуск backend с понятной ошибкой.

## Docker и деплой

В корне лежит `Dockerfile` ([ADR-004](docs/decisions/004-docker-render-deploy.md)): один образ, один процесс. FastAPI раздаёт и API, и собранный frontend (статический экспорт Next.js) с одного origin на порту из переменной `PORT` (по умолчанию 8000).

```bash
make docker-build                                   # собрать образ cal-app
PORT=8000 make docker-run                           # запустить: страницы и /health работают и без БД
DATABASE_URL=postgres://cal:cal@host.docker.internal:5432/cal \
  RUN_MIGRATIONS=true SEED_ON_START=true PORT=8000 make docker-run   # с БД из `make up`
```

`DATABASE_URL` принимает `postgres://` и `postgresql://` (так отдают облачные БД). `RUN_MIGRATIONS=true` применяет миграции перед стартом (ошибка останавливает контейнер), `SEED_ON_START=true` идемпотентно создаёт типы событий на 30 и 60 минут. Бесплатный деплой на Render (веб-сервис из Dockerfile и Postgres) описан в ADR-004.

## Правила бронирования

- Слоты начинаются на сетке 30 минут и целиком лежат в рабочем интервале; окно записи — сегодня и ещё 13 дней по календарю владельца.
- Никакие две встречи, даже разных типов, не пересекаются по времени. Правило выполняется на сервере: время проверяется функцией слотов, а непересечение гарантирует ограничение PostgreSQL, поэтому одновременные запросы тоже не создают двойную запись (второй получает `409 slot_taken`).
- Гость видит время в поясе владельца или в своём (переключатель на экране).

## AI-подбор слотов

Backend умеет подбирать слоты по фразе («на следующей неделе в обед по понедельникам»): `POST /api/v1/slot-suggestions`, агент LangChain с одним инструментом поиска слотов, слоты проверяются функцией слотов ([ADR-003](docs/decisions/003-ai-agent-langchain.md)). Нужен `AI_API_KEY`. **Вкладка «Подобрать с AI» на экране пока не подключена** (отложена, см. [roadmap](docs/roadmap.md)).

## Как проверить требования задания

| # | Требование | Как проверить |
|---|------------|---------------|
| 1 | Backend и frontend запускаются локально | Шаги из раздела «Установка и запуск»; `curl localhost:8000/health` даёт `{"status":"ok"}`, на http://localhost:3000 — экран записи |
| 2 | Есть команды тестов и линтера | `make help` показывает их; `make test` и `make lint` завершаются с кодом 0 |
| 3 | GitHub Actions прогоняет тесты и линтер на каждый push, прогон зелёный | Вкладка Actions → workflow **CI** (jobs Backend и Frontend) зелёный на последнем коммите; `gh run list --workflow ci.yml` |
| 4 | Conventional Commits; release-please создаёт release-PR после мержа в `main` | `git log --oneline` — все коммиты вида `type(scope): ...`; после мержа в `main` во вкладке Pull Requests появляется PR `chore(main): release X.Y.Z` от `release-please` |
| 5 | В корне есть `AGENTS.md` с командами запуска, тестов, линтера и правилом про формат коммитов | Открыть [AGENTS.md](AGENTS.md) |

## Как работает release-please

1. Вы пишете коммиты по Conventional Commits и мержите PR в `main` (squash — заголовок PR становится коммитом).
2. Workflow `release-please.yml` на каждый push в `main` читает коммиты с прошлого релиза. `fix:` поднимает patch, `feat:` — minor, `feat!:` / `BREAKING CHANGE` — major (пока версия 0.x, minor/major сдвигаются осторожнее). `chore:`, `docs:` версию не поднимают.
3. Если есть релизные коммиты, бот открывает (и потом обновляет) **release-PR** `chore(main): release X.Y.Z`: в нём новая версия в `.release-please-manifest.json` и дописанный `CHANGELOG.md`.
4. Вы мержите release-PR вручную — тогда создаются git-тег и GitHub Release. Пока не смержили, PR просто копит изменения.

**Где смотреть и что проверять**

- **Release-PR** — вкладка Pull Requests: PR `chore(main): release X.Y.Z` от `github-actions`, ветка `release-please--branches--main`. Это и есть «релиз» на этапе проверки задания: он появляется после мержа в `main` коммита `feat`/`fix`.
- **Запуск workflow** — вкладка Actions → `release-please`: прогон на push в `main` должен быть зелёным.
- **GitHub Release и тег** (`vX.Y.Z`, вкладка Releases) появятся только после мержа самого release-PR. Пока его не смержили — релизов нет, и это нормально. Для каркаса release-PR можно не мержить.
- **Если release-PR нет:** в `main` не было `feat`/`fix` коммитов (только `chore`/`docs`) либо выключена настройка Settings → Actions → General → «Allow GitHub Actions to create and approve pull requests».

Конфиг: `release-please-config.json`, `.release-please-manifest.json`. Нужна настройка репозитория: Settings → Actions → General → «Allow GitHub Actions to create and approve pull requests».

---

<details>
<summary>Автоматические тесты Хекслета</summary>

Тесты запускаются на каждый коммит. За запуск отвечает файл `.github/workflows/hexlet-check.yml` — не удаляйте и не переименовывайте ни его, ни репозиторий.

</details>

## О Хекслете

[Хекслет](https://ru.hexlet.io/) — школа программирования: авторские программы обучения с практикой, поддержкой наставников и реальными проектами, которые остаются в резюме. Этот репозиторий — один из таких проектов.
