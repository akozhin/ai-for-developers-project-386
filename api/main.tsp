import "@typespec/http";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

/**
 * Контракт API «Запись на звонок». Единственный источник правды (Design First, ADR-002):
 * любое изменение API начинается здесь, затем перегенерируется `openapi.yaml`.
 *
 * Авторизации нет: владелец — один заранее заданный профиль, гость записывается без входа.
 * Время — ISO 8601 в UTC, даты календаря — `YYYY-MM-DD` по часовому поясу владельца.
 */
@service(#{ title: "Запись на звонок" })
@info(#{ version: "1.0.0" })
@server("http://localhost:8000", "Локальный backend")
namespace CallBooking;

// ───────────────────────── Общие типы ─────────────────────────

/** Читаемый идентификатор типа события: его задаёт владелец, он же в публичной ссылке. */
@pattern("^[a-z0-9]+(-[a-z0-9]+)*$")
@minLength(1)
@maxLength(64)
scalar EventTypeId extends string;

/** Свободный интервал времени под тип события. */
@example(#{
  starts_at: utcDateTime.fromISO("2026-10-12T08:00:00Z"),
  ends_at: utcDateTime.fromISO("2026-10-12T08:30:00Z"),
})
model Slot {
  starts_at: utcDateTime;
  ends_at: utcDateTime;
}

// ───────────────────────── Ошибки ─────────────────────────

/** Ошибка поля в теле запроса. */
@example(#{ field: "guest_email", message: "Некорректный email" })
model FieldError {
  field: string;
  message: string;
}

/** Тип события не найден (в том числе некорректный id в пути). */
@error
model EventTypeNotFound {
  @statusCode _: 404;
  code: "event_type_not_found";
  message: string;
}

/** Время пересекается с существующим бронированием любого типа. */
@error
model SlotTaken {
  @statusCode _: 409;
  code: "slot_taken";
  message: string;
}

/** Время не является доступным слотом (прошлое, запас до записи, вне окна, вне рабочих часов, не на сетке). */
@error
model SlotNotAvailable {
  @statusCode _: 409;
  code: "slot_not_available";
  message: string;
}

/** Тип события с таким id уже существует. */
@error
model EventTypeExists {
  @statusCode _: 409;
  code: "event_type_exists";
  message: string;
}

/** Ошибка валидации полей запроса. */
@error
model ValidationError {
  @statusCode _: 422;
  code: "validation_error";
  message: string;
  fields: FieldError[];
}

/** Превышен лимит запросов к AI. */
@error
model RateLimited {
  @statusCode _: 429;
  code: "rate_limited";
  message: string;
}

/** AI не настроен, недоступен или не успел ответить. */
@error
model AiUnavailable {
  @statusCode _: 503;
  code: "ai_unavailable";
  message: string;
}

// ───────────────────────── Система ─────────────────────────

/** Состояние сервиса. */
model Health {
  status: "ok";
}

@tag("system")
@route("/health")
interface System {
  /** Проверка работоспособности (без версии в пути). */
  @get
  @operationId("getHealth")
  health(): Health;
}

// ───────────────────────── Типы событий ─────────────────────────

/** Тип события: вид звонка, который предлагает владелец. */
@example(#{
  id: "call-30",
  title: "Звонок 30 минут",
  description: "Короткий созвон: знакомство или быстрый вопрос",
  duration_minutes: 30,
})
@extension("additionalProperties", false)
model EventType {
  /** Читаемый идентификатор; задаёт владелец, уникален. */
  id: EventTypeId;

  @minLength(1)
  @maxLength(100)
  title: string;

  @minLength(1)
  @maxLength(500)
  description: string;

  /** Длительность в минутах. */
  @minValue(5)
  @maxValue(480)
  duration_minutes: int32;
}

model EventTypeList {
  items: EventType[];
}

@tag("event-types")
@route("/api/v1/event-types")
interface EventTypes {
  /** Список типов событий (гость и владелец). Пустой список — `200` с `items: []`. */
  @get
  @operationId("listEventTypes")
  list(): EventTypeList;

  /** Создать тип события (владелец, без авторизации). */
  @post
  @operationId("createEventType")
  create(@body body: EventType):
    | {
        @statusCode _: 201;
        @body body: EventType;
      }
    | EventTypeExists
    | ValidationError;

  /** Один тип события. */
  @route("{id}")
  @get
  @operationId("getEventType")
  get(@path id: string): EventType | EventTypeNotFound;

  /** Свободные слоты типа события на все 14 дней окна записи, по дням. */
  @route("{id}/slots")
  @get
  @operationId("getEventTypeSlots")
  slots(@path id: string): SlotsResponse | EventTypeNotFound;
}

// ───────────────────────── Слоты ─────────────────────────

/** Свободные слоты одного календарного дня владельца. */
@example(#{
  date: plainDate.fromISO("2026-10-12"),
  slots: #[
    #{
      starts_at: utcDateTime.fromISO("2026-10-12T08:00:00Z"),
      ends_at: utcDateTime.fromISO("2026-10-12T08:30:00Z"),
    }
  ],
})
model SlotDay {
  /** Дата по календарю владельца. */
  date: plainDate;

  /** Свободные слоты; нерабочий или занятый день — пустой список. */
  slots: Slot[];
}

/** Окно записи: всегда все 14 дней, начиная с текущей даты. */
model SlotsResponse {
  /** Часовой пояс владельца (IANA), по нему считаются границы дней. */
  timezone: string;

  @minItems(14)
  @maxItems(14)
  days: SlotDay[];
}

// ───────────────────────── Бронирования ─────────────────────────

/** Данные для бронирования слота. */
@example(#{
  event_type_id: "call-30",
  starts_at: utcDateTime.fromISO("2026-10-12T08:00:00Z"),
  guest_name: "Анна",
  guest_email: "anna@example.com",
  comment: "Хочу обсудить проект",
})
@extension("additionalProperties", false)
model BookingInput {
  event_type_id: EventTypeId;

  /** Начало слота; должно совпадать со слотом из выдачи слотов. */
  starts_at: utcDateTime;

  @minLength(1)
  @maxLength(100)
  guest_name: string;

  @format("email")
  @maxLength(254)
  guest_email: string;

  @maxLength(500)
  comment?: string;
}

/** Бронирование (встреча в списке владельца). */
@example(#{
  id: "0b8f6e1c-5f0a-4c53-9d7e-2d4e6f8a1b3c",
  event_type: #{
    id: "call-30",
    title: "Звонок 30 минут",
    description: "Короткий созвон: знакомство или быстрый вопрос",
    duration_minutes: 30,
  },
  starts_at: utcDateTime.fromISO("2026-10-12T08:00:00Z"),
  ends_at: utcDateTime.fromISO("2026-10-12T08:30:00Z"),
  guest_name: "Анна",
  guest_email: "anna@example.com",
  comment: "Хочу обсудить проект",
  created_at: utcDateTime.fromISO("2026-10-09T12:00:00Z"),
})
model Booking {
  @format("uuid")
  id: string;

  event_type: EventType;
  starts_at: utcDateTime;
  ends_at: utcDateTime;

  @minLength(1)
  @maxLength(100)
  guest_name: string;

  @format("email")
  @maxLength(254)
  guest_email: string;

  @maxLength(500)
  comment?: string;

  created_at: utcDateTime;
}

model BookingList {
  items: Booking[];
}

@tag("bookings")
@route("/api/v1/bookings")
interface Bookings {
  /** Забронировать слот (гость). */
  @post
  @operationId("createBooking")
  create(@body body: BookingInput):
    | {
        @statusCode _: 201;
        @body body: Booking;
      }
    | EventTypeNotFound
    | SlotTaken
    | SlotNotAvailable
    | ValidationError;

  /** Предстоящие встречи всех типов по возрастанию начала (владелец). */
  @get
  @operationId("listBookings")
  list(): BookingList;
}

// ───────────────────────── Профиль ─────────────────────────

/** Профиль владельца календаря. */
@example(#{
  name: "Alexandr Kozhin",
  timezone: "Europe/Moscow",
  avatar_url: "/avatar.jpg",
  ai_enabled: true,
})
model Profile {
  name: string;

  /** Часовой пояс владельца (IANA). */
  timezone: string;

  /** Адрес аватара или `null` (тогда показываются инициалы). */
  avatar_url: string | null;

  /** AI-подбор настроен: вкладка «Подобрать с AI» видна только при `true`. */
  ai_enabled: boolean;
}

@tag("profile")
@route("/api/v1/profile")
interface ProfileApi {
  /** Профиль владельца для шапки главного экрана. */
  @get
  @operationId("getProfile")
  get(): Profile;
}

// ───────────────────────── AI-подбор слотов ─────────────────────────

/** Пожелание гостя, описанное текстом. */
@example(#{
  event_type_id: "call-30",
  text: "На следующей неделе могу в понедельник, среду или пятницу в обед",
  timezone: "Europe/Moscow",
})
@extension("additionalProperties", false)
model SlotSuggestionInput {
  event_type_id: EventTypeId;

  @minLength(1)
  @maxLength(500)
  text: string;

  /** Часовой пояс гостя на экране (IANA): в нём трактуются «в обед», «утром». */
  timezone: string;
}

/** Предложенный слот. */
model SuggestedSlot {
  ...Slot;

  /** Лучший вариант; ровно один в непустом ответе. */
  recommended: boolean;
}

/** Ответ агента: короткий текст и до трёх подходящих слотов. */
@example(#{
  text: "Нашёл три варианта на следующей неделе в обед",
  items: #[
    #{
      starts_at: utcDateTime.fromISO("2026-10-12T09:30:00Z"),
      ends_at: utcDateTime.fromISO("2026-10-12T10:00:00Z"),
      recommended: true,
    }
  ],
})
model SlotSuggestionResponse {
  text: string;

  /** Только реально свободные слоты; пустой список, если ничего не подошло. */
  @maxItems(3)
  items: SuggestedSlot[];
}

@tag("slot-suggestions")
@route("/api/v1/slot-suggestions")
interface SlotSuggestions {
  /** Подобрать слоты по пожеланию гостя с помощью AI-агента. */
  @post
  @operationId("createSlotSuggestion")
  create(@body body: SlotSuggestionInput):
    | SlotSuggestionResponse
    | EventTypeNotFound
    | ValidationError
    | RateLimited
    | AiUnavailable;
}
