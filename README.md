# Календарь звонков


[![hexlet-check](https://github.com/akozhin/ai-for-developers-project-386/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/akozhin/ai-for-developers-project-386/actions)

Разработайте совместно с ИИ сервис для бронирования календаря

Учебный проект Хекслета: https://ru.hexlet.io/programs/ai-for-developers
Как это должно работать: https://files.hexlet.app/a/2ipc5m

## Как это выглядит

Упрощённый Cal.com: владелец публикует типы звонков, гость выбирает свободный слот на ближайшие 14 дней и записывается без регистрации. Двойное бронирование исключено — две встречи не пересекаются, даже если это разные типы.

![Экран записи: календарь, слоты и форма подтверждения](docs/mockups/main.png)

А ещё можно просто написать, когда удобно, и AI-агент подберёт подходящие слоты:

![Режим «Подобрать с AI»](docs/mockups/book.png)

> Это макеты: реализация идёт по [спецификации](https://github.com/akozhin/ai-for-developers-project-386/issues/14). Решения — в [docs/decisions/](docs/decisions/), словарь — в [GLOSSARY.md](GLOSSARY.md).

## Стек

- **Backend:** Python 3.12, uv, FastAPI, SQLAlchemy 2 async, Alembic, PostgreSQL
- **Frontend:** Next.js, React, TypeScript, Tailwind 4, shadcn/ui, pnpm
- **Качество:** ruff, mypy, ESLint, Prettier, pytest, Vitest
- **CI/CD:** GitHub Actions, release-please
- Документация и методология: [docs/](docs/README.md)

## Установка

Нужны `uv`, `pnpm` (Node 24), `make`.

```bash
git clone https://github.com/akozhin/ai-for-developers-project-386.git
cd ai-for-developers-project-386
make install
```

## Использование

```bash
make help           # список всех команд
make dev-backend    # http://localhost:8000/health -> {"status":"ok"}
make dev-frontend   # http://localhost:3000
make test           # тесты backend (pytest) и frontend (Vitest)
make lint           # линтеры backend (ruff) и frontend (ESLint, Prettier)
make ci             # lint + typecheck + test + build, как в CI
```

Полный список команд и правила для агентов — в [AGENTS.md](AGENTS.md).

## Как проверить требования задания

| # | Требование | Как проверить |
|---|------------|---------------|
| 1 | Backend и frontend запускаются локально | `make install`, затем `make dev-backend` и `curl localhost:8000/health` (ждём `{"status":"ok"}`); `make dev-frontend` и открыть http://localhost:3000 — заголовок «Запись на звонок» |
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
