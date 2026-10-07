# Sprint 01: Каркас и CI

> **Версия roadmap:** v0.1
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-10-07
> **Закрыт:** 2026-10-07

---

## Цель спринта

Проект собирается, проверяется и релизится автоматически: пустой, но рабочий backend и frontend под CI.

---

## DoD спринта

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Backend стартует, `/health` отвечает 200 | `curl localhost:8000/health` |
| 2 | Frontend собирается и открывается | `make build`, страница показывает «Запись на звонок» |
| 3 | Дымовые тесты проходят | `make test` |
| 4 | Линтеры и типы проходят | `make lint typecheck` |
| 5 | CI зелёный на push | вкладка Actions / `gh run list` |
| 6 | После мержа в `main` появляется release-PR | `gh pr list` |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | Каркас, тесты, линтеры, CI и release-please | ✅ | [plan](tasks/01-scaffold-ci/plan.md) | [summary](tasks/01-scaffold-ci/summary.md) |

---

## Задача 01: Каркас, тесты, линтеры, CI и release-please ✅

### Цель

Выполнить первое задание проекта целиком: стек, каркас backend и frontend, тестовый раннер, линтеры, GitHub Actions и release-please.

> 💡 **Скиллы:** `modern-python`, `uv-package-manager`, `fastapi-templates`, `nextjs-app-router-patterns`, `shadcn`, `github-actions-templates`.

### Состав работ

Подробно — в [plan.md](tasks/01-scaffold-ci/plan.md).

### Пользователь проверяет

См. чек-лист «Пользователь проверяет вручную» в [plan.md](tasks/01-scaffold-ci/plan.md) и таблицу в [README проекта](../../../README.md#как-проверить-требования-задания).

### Документы

- 📋 [План задачи](tasks/01-scaffold-ci/plan.md)
- 📝 [Summary](tasks/01-scaffold-ci/summary.md)

---

## Итог

Каркас backend и frontend, дымовые тесты, линтеры, CI на каждый push и release-please работают. PR #1 смержен, release-PR #2 создан. Отклонения и версии — в [summary](tasks/01-scaffold-ci/summary.md). В следующий спринт: БД, API бронирования.
