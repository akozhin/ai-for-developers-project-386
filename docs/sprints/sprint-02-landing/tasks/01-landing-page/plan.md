# Task 01: Главная страница с типами звонков на моках

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** feat
> **Ветка:** `feat/frontend-landing-page`
> **Spec:** без spec (решения — в grill-сессии, итог ниже)

---

## Цель

Главная `/` рассказывает про сервис, показывает типы звонков (серверный `fetch` к `GET /api/v1/event-types`, пока на моках MSW) и ведёт кнопкой «Записаться» на `/book`, где пока заглушка.

Термины — по [GLOSSARY.md](../../../../../GLOSSARY.md): на странице «звонок» и «записаться», без «бронирование», «встреча», «заявка».

---

## Решения

| Тема | Решение |
|------|---------|
| Содержимое `/` | hero + кнопка «Записаться»; «Как это работает» (3 шага); преимущества («без регистрации», «двойная запись исключена»); подвал «учебный проект». Ссылки на страницу владельца нет |
| Кнопка | Ссылка `<Link href="/book">` со стилем `buttonVariants()` (в `Button` — base-ui, `asChild` нет); тест по роли `link` |
| `/book` | Заглушка `app/book/page.tsx`: заголовок и ссылка «назад». Реальный выбор слота — в sprint «UI» |
| Данные | Серверный `fetch` `GET ${API_URL}/api/v1/event-types`, `next: { revalidate: 60 }`. Только список типов, карточки некликабельные |
| Форма ответа | `{ "items": [ { "id": "uuid", "title": "…", "duration_minutes": 30 } ] }` — дописать в `api-contracts.md` |
| Состояния блока | данные → карточки «название · N минут»; `items: []` → «Владелец пока не добавил типы звонков»; ошибка (сеть, не-2xx, невалидный JSON) → блок скрыт, ошибка в серверный лог |
| Моки | MSW (`msw/node`), дефолт: «Консультация · 30 мин», «Разбор кода · 60 мин». Пустой ответ и 500 — через `server.use(...)` в тестах |
| Моки в dev | `instrumentation.ts` поднимает MSW при `MOCK_API=true` и `NODE_ENV !== "production"` |
| Переменные | `API_URL=http://localhost:8000` (без `NEXT_PUBLIC_`), `MOCK_API=true` — в `frontend/.env.example` |
| Нумерация | Backend-ядро сдвигается с sprint-02 на sprint-03 (roadmap, `api-contracts.md`) |

### Техническое решение (уточнено при реализации)

В проекте включён `cacheComponents` (Next 16): `fetch` вне `<Suspense>` ломает сборку, `next.revalidate` не действует, кеш задаётся через `use cache` + `cacheLife`. Vitest не рендерит `async` Server Components ([Next docs](../../../../../frontend/node_modules/next/dist/docs/01-app/02-guides/testing/vitest.md)). Поэтому:

- `lib/api/event-types.ts` — `getEventTypes(): Promise<EventType[] | null>` (`null` = ошибка, лог на сервере). Внутри `fetchEventTypes` с `use cache` и `cacheLife({ revalidate: 60 })`; ошибки в кеш не попадают.
- `components/event-types-section.tsx` — синхронный компонент трёх состояний.
- `components/event-types-loader.tsx` — async-обёртка: `await connection()` (данные при запросе, а не при сборке) + `getEventTypes()`; на главной внутри `<Suspense fallback={null}>`.
- `app/page.tsx` — синхронная; тесты: `render(<Home />)`, загрузчик — `render(await EventTypesLoader())`.

---

## Состав работ

- [x] `GLOSSARY.md` (уже создан в grill-сессии) — закоммитить
- [x] `docs/concept/api-contracts.md`: схема ответа `GET /event-types`; колонка «Спринт» 02 → 03 для backend-эндпоинтов
- [x] `pnpm add -D msw` в `frontend/`; проверить, что `make install` (`--frozen-lockfile`) проходит
- [x] `frontend/mocks/` — handlers, `server`; `tests/setup.ts` — запуск/сброс/остановка сервера
- [x] `lib/api/event-types.ts` + тесты (данные, пусто, 500, сеть, невалидное тело)
- [x] `components/event-types-section.tsx` + тесты трёх состояний
- [x] `app/page.tsx`: hero, три шага, преимущества, подвал, ссылка на `/book`; обновить `tests/home.test.tsx`
- [x] `app/book/page.tsx` + тест
- [x] `instrumentation.ts` (MSW при `MOCK_API=true`, не в production)
- [x] `frontend/.env.example`, исключение `!.env.example` в `frontend/.gitignore`; `API_URL` / `MOCK_API` в README frontend
- [x] `metadata` в `layout.tsx` — актуальное описание
- [x] Самопроверка по DoD, вручную в браузере (`.claude/launch.json`, :3100)
- [ ] (после «ок» пользователя) `summary.md`, README спринта, `docs/roadmap.md`

Порядок: тесты вперёд (TDD) для `getEventTypes` и `EventTypesSection`, затем страницы.

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | На `/` есть `h1`, три шага «Как это работает», ссылка «Записаться» с `href="/book"` | `tests/home.test.tsx` |
| 2 | Блок типов звонков: данные / пусто / ошибка | `tests/event-types-section.test.tsx`, `tests/event-types.test.ts`, `tests/event-types-loader.test.tsx` |
| 3 | `/book` отдаёт заглушку со ссылкой назад | `tests/book.test.tsx` |
| 4 | С `MOCK_API=true` главная показывает два мок-типа | `make dev-frontend`, открыть `/` |
| 5 | В production-сборке моки не подключаются | код `instrumentation.ts`; `make build` проходит |
| 6 | Тесты, линтеры, типы, сборка | `make ci` |

### Пользователь проверяет вручную

- [x] `/` рассказывает про сервис, есть блок «Какие звонки можно заказать» с двумя карточками
- [x] Кнопка «Записаться» открывает `/book` с заглушкой; ссылка «назад» возвращает на `/`
- [x] При `MOCK_API=false` без backend главная открывается, блок типов скрыт, кнопка работает

---

## Артефакты

- `GLOSSARY.md`
- `frontend/app/page.tsx`, `frontend/app/book/page.tsx`, `frontend/app/layout.tsx` (metadata)
- `frontend/components/event-types-section.tsx`, `frontend/components/event-types-loader.tsx`
- `frontend/lib/api/event-types.ts`
- `frontend/mocks/` (handlers, server), `frontend/instrumentation.ts`
- `frontend/tests/` (`setup.ts`, `home`, `book`, `event-types`, `event-types-section`, `event-types-loader`)
- `frontend/package.json`, `frontend/pnpm-lock.yaml` (msw), `frontend/.env.example`, `frontend/.gitignore`, `frontend/README.md`
- `docs/concept/api-contracts.md`, `docs/roadmap.md`, `docs/sprints/sprint-02-landing/`

---

## Scope

**Трогаем:** только файлы из «Артефактов».

**НЕ трогаем:**
- `.github/workflows/hexlet-check.yml`
- `backend/` (эндпоинта `/event-types` там нет, он в sprint-03)
- Лого, шапку, тёмную тему, SEO сверх `metadata`, ссылки на карточках, ближайшие слоты

---

## Риски и допущения

- Next 16.4 отличается от привычных версий: перед `instrumentation.ts` и `fetch`-кешем перечитать `frontend/node_modules/next/dist/docs/` (`instrumentation.md`, `fetch.md`).
- MSW в Next-инструментации: регистрация только в `NEXT_RUNTIME === "nodejs"`, через динамический `import`, чтобы MSW не попал в edge-/production-бандл. Если не заработает, fallback — `fetch` на локальный мок-сервер (обсудим до реализации).
- Строгие линтеры (`no any`, `@ts-ignore` запрещены): ответ API валидируется вручную type-guard, без `as`.
- `frontend/.gitignore` игнорирует `.env*` — нужен `!.env.example`.
- `pnpm-workspace.yaml` может требовать разрешения build-скриптов для `msw`.
- Контракт `GET /event-types` не реализован в backend: моки — единственный источник формы ответа до sprint-03.

---

## Открытые вопросы

- [x] Нет.
