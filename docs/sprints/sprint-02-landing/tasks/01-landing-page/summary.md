# Summary: Task 01 — Главная страница с типами звонков на моках

> **План:** [plan.md](./plan.md)
> **PR:** ещё не открыт (ветка `feat/frontend-landing-page`)
> **Дата закрытия:** 2026-10-09

---

## Что реализовано

- `frontend/app/page.tsx` — главная: hero с кнопкой «Записаться» (ссылка на `/book`), «Как это работает» (3 шага), блок типов звонков, «Почему удобно», подвал
- `frontend/app/book/page.tsx` — заглушка «Выбор времени» со ссылкой «Назад»
- `frontend/lib/api/event-types.ts` — `getEventTypes()`: `fetch` к `GET /api/v1/event-types`, кеш 60 с (`use cache` + `cacheLife`), ручная валидация ответа, `null` при ошибке
- `frontend/components/event-types-section.tsx` (карточки / пусто / скрыт при ошибке) и `event-types-loader.tsx` (`connection()` + `<Suspense>`)
- MSW: `frontend/mocks/` (два мок-типа), `instrumentation.ts` (только при `MOCK_API=true` вне production), подключение в `tests/setup.ts`
- `frontend/.env.example` (`API_URL`, `MOCK_API`), раздел в `frontend/README.md`
- `GLOSSARY.md`: Владелец, Гость, Тип звонка, Слот, Запись
- `docs/concept/api-contracts.md`: схема `GET /event-types`, backend-эндпоинты → sprint-03
- 14 тестов Vitest (было 1)

---

## Отклонения от плана

- Включён `cacheComponents`: `next.revalidate` у `fetch` не действует, запрос вне `<Suspense>` ломает сборку. Вместо `revalidate: 60` — `use cache` + `cacheLife`, загрузка вынесена в `EventTypesLoader` с `connection()`. Главная осталась синхронной.
- Взят `msw@^2`, а не 3.x: Vitest 5 ожидает `^2.4.9`.
- В `tests/setup.ts` добавлен `cleanup()` (в Vitest не включены `globals`, RTL сам DOM не чистит).
- Два `as Record<string, unknown>` в type-guard ответа API (сужение типа; `any` и `@ts-ignore` нет), хотя план обещал «без `as`».
- Postinstall `msw` проигнорирован pnpm (нужен только браузерному воркеру); `pnpm-workspace.yaml` не менялся.

---

## Принятые решения

| Решение | Причина | Ссылка на ADR |
|---------|---------|--------------|
| Моки через MSW, общие для тестов и dev | Один контракт без дублирующего мок-API в Next; после sprint-03 достаточно `MOCK_API=false` | — |
| Ошибка API скрывает блок, а не страницу | Кнопка записи должна работать при любой доступности backend | — |
| Карточки типов звонков некликабельные | YAGNI: выбор типа — часть страницы `/book` | — |
| Нумерация: главная — sprint-02, backend-ядро — sprint-03, UI — sprint-04 | Frontend-фича не из ядра бронирования | — |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `make build` падал: uncached `fetch` вне `<Suspense>` при `cacheComponents` | `use cache` + `cacheLife`, `EventTypesLoader` с `connection()` внутри `<Suspense>` |
| Тесты видели элементы предыдущих тестов | `cleanup()` в `afterEach` |
| Vitest не рендерит async Server Components | async-логика разделена: тестируются `getEventTypes`, синхронная секция, `await EventTypesLoader()` |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `h1`, 3 шага, ссылка «Записаться» → `/book` | ✅ `tests/home.test.tsx`, браузер |
| 2 | Блок типов звонков: данные / пусто / ошибка | ✅ `event-types*.test.ts(x)` |
| 3 | `/book` — заглушка со ссылкой назад | ✅ `tests/book.test.tsx`, переход в браузере |
| 4 | `MOCK_API=true` показывает два мок-типа | ✅ `make dev-frontend` (:3100) |
| 5 | Моки не в production | ✅ проверка в `instrumentation.ts`, `make build` проходит |
| 6 | `make ci` | ✅ exit 0, 14 тестов |

Дополнительно: при `MOCK_API=false` без backend главная открывается, блок скрыт, ошибка в серверном логе.

---

## Версии (на 2026-10-09)

| Компонент | Версия |
|-----------|--------|
| Next.js, React | 16.4.0, 19.3.0 |
| msw | 2.15.0 |
| Vitest | 5.0.3 |

---

## Что дальше

Sprint 03 «Ядро бронирования»: PostgreSQL, Alembic, API типов звонков, слотов и записей. Когда `GET /api/v1/event-types` появится в backend, в `.env.local` ставится `MOCK_API=false`. Sprint 04 «UI»: наполнить `/book` (тип звонка → дата → слот → имя и email) и страницу владельца.
