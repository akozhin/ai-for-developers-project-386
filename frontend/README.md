# Frontend

Next.js 16 (App Router), React, TypeScript, Tailwind 4, shadcn/ui, pnpm. Тонкий UI: вся бизнес-логика (слоты, бронирование) — в backend.

- `/` — экран записи гостя: профиль владельца, тип события, календарь на 14 дней, слоты, форма и подтверждение (`components/booking/`).
- `/admin` — страница владельца: предстоящие встречи по месяцам и типы событий (`components/admin/`), без авторизации.
- Запросы идут через SDK, сгенерированный из `api/openapi.yaml` (`lib/api/generated`, руками не правится; `make generate` из корня репозитория), на тот же origin; Next.js проксирует `/api/v1/*` на backend (`API_URL`, по умолчанию `http://localhost:8000`).
- Тесты (Vitest + Testing Library + MSW) — `tests/`, типизированные моки — `mocks/`.

Команды запускаются из корня репозитория: `make dev-frontend`, `make test-frontend`, `make lint-frontend`, `make typecheck-frontend`, `make build`. Перед правками Next.js читайте [AGENTS.md](AGENTS.md): версия отличается от привычных.
