# Архитектура

---

## 1. Компоненты и ответственность

| Компонент | Ответственность | Не отвечает за |
|-----------|-----------------|----------------|
| Frontend (Next.js) | UI, запросы к API, отображение слотов | Расчёт слотов, правила бронирования |
| Backend (FastAPI) | Бизнес-логика, валидация, REST API | Рендеринг UI |
| PostgreSQL | Хранение, гарантия уникальности слота | Бизнес-правила |

Бизнес-логика живёт **только в backend**.

---

## 2. Контейнеры

```mermaid
graph TB
    Browser[Браузер] -->|HTTP| FE[frontend :3000]
    FE -->|REST /api/v1| BE[backend :8000]
    BE -->|asyncpg| DB[(postgres :5432)]
```

---

## 3. Последовательность: бронирование слота

```mermaid
sequenceDiagram
    participant G as Гость
    participant FE as Frontend
    participant BE as Backend
    participant DB as PostgreSQL

    G->>FE: Открывает страницу типа звонка
    FE->>BE: GET /api/v1/event-types/{id}/slots?date=...
    BE->>DB: правила доступности + занятые записи
    BE-->>FE: список свободных слотов
    G->>FE: Выбирает слот, вводит имя и email
    FE->>BE: POST /api/v1/bookings
    BE->>DB: INSERT booking (UNIQUE по слоту)
    alt слот свободен
        BE-->>FE: 201 Created
    else слот занят
        BE-->>FE: 409 Conflict
    end
```

---

## 4. Деплой

Локально: `docker-compose.yml` поднимает PostgreSQL; backend и frontend запускаются через `make dev`. Продовый деплой — вне scope первых спринтов (см. [roadmap](../roadmap.md)).

---

## 5. Репозиторий и релизы

Монорепо. CI (`.github/workflows/ci.yml`) прогоняет линтеры, типы и тесты на каждый push. `release-please` формирует release-PR по Conventional Commits после мержа в `main`.
