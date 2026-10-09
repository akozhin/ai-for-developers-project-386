import { http, HttpResponse } from "msw";

import type {
  Booking,
  BookingInput,
  EventType,
  EventTypeList,
  Profile,
  Slot,
  SlotsResponse,
} from "@/lib/api/generated";

/** Адрес, на котором SDK работает в тестах (`NEXT_PUBLIC_API_BASE_URL` в vitest.config). */
export const API = "http://localhost:3000/api/v1";

export const mockProfile: Profile = {
  name: "Alexandr Kozhin",
  timezone: "Europe/Moscow",
  avatar_url: "/avatar.jpg",
  ai_enabled: false,
};

export const call30: EventType = {
  id: "call-30",
  title: "Консультация",
  description: "Короткий созвон: знакомство или быстрый вопрос",
  duration_minutes: 30,
};

export const call60: EventType = {
  id: "call-60",
  title: "Разбор кода",
  description: "Подробный разбор задачи или проекта",
  duration_minutes: 60,
};

const WINDOW_START = "2026-10-12"; // понедельник

export function slot(startsAt: string, minutes: number): Slot {
  const end = new Date(new Date(startsAt).getTime() + minutes * 60_000);
  return {
    starts_at: startsAt,
    ends_at: end.toISOString().replace(".000Z", "Z"),
  };
}

function addDays(date: string, days: number): string {
  const next = new Date(`${date}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + days);
  return next.toISOString().slice(0, 10);
}

/** 14 дней окна: слоты только в дни из `slotsByDate` (даты по календарю владельца, Москва). */
export function slotsResponse(
  slotsByDate: Record<string, Slot[]>,
  windowStart: string = WINDOW_START,
): SlotsResponse {
  return {
    timezone: "Europe/Moscow",
    // Контракт требует ровно 14 дней, SDK описывает это кортежем.
    days: Array.from({ length: 14 }, (_, offset) => {
      const date = addDays(windowStart, offset);
      return { date, slots: slotsByDate[date] ?? [] };
    }) as SlotsResponse["days"],
  };
}

/** 30 минут: пн 12 (3 слота), вт 13 (3 слота, один «рано» в 06:30 МСК), чт 15 (1 слот). */
export const slots30 = slotsResponse({
  "2026-10-12": [
    slot("2026-10-12T07:00:00Z", 30),
    slot("2026-10-12T07:30:00Z", 30),
    slot("2026-10-12T08:00:00Z", 30),
  ],
  "2026-10-13": [
    slot("2026-10-13T03:30:00Z", 30),
    slot("2026-10-13T07:00:00Z", 30),
    slot("2026-10-13T07:30:00Z", 30),
  ],
  "2026-10-15": [slot("2026-10-15T09:00:00Z", 30)],
});

/** 60 минут: только пн 12 и вт 13 по одному слоту. */
export const slots60 = slotsResponse({
  "2026-10-12": [slot("2026-10-12T07:00:00Z", 60)],
  "2026-10-13": [slot("2026-10-13T07:00:00Z", 60)],
});

export function bookingFor(input: BookingInput, eventType: EventType): Booking {
  return {
    id: "0b8f6e1c-5f0a-4c53-9d7e-2d4e6f8a1b3c",
    event_type: eventType,
    starts_at: input.starts_at,
    ends_at: slot(input.starts_at, eventType.duration_minutes).ends_at,
    guest_name: input.guest_name,
    guest_email: input.guest_email,
    comment: input.comment,
    created_at: "2026-10-12T06:00:00Z",
  };
}

/** Ответы бэкенда по умолчанию: профиль, два типа, слоты, успешное бронирование. */
export const bookingScreenHandlers = [
  http.get(`${API}/profile`, () => HttpResponse.json<Profile>(mockProfile)),
  http.get(`${API}/event-types`, () =>
    HttpResponse.json<EventTypeList>({ items: [call30, call60] }),
  ),
  http.get(`${API}/event-types/call-30/slots`, () =>
    HttpResponse.json<SlotsResponse>(slots30),
  ),
  http.get(`${API}/event-types/call-60/slots`, () =>
    HttpResponse.json<SlotsResponse>(slots60),
  ),
  http.post(`${API}/bookings`, async ({ request }) => {
    const input = (await request.json()) as BookingInput;
    const eventType = input.event_type_id === "call-60" ? call60 : call30;
    return HttpResponse.json<Booking>(bookingFor(input, eventType), {
      status: 201,
    });
  }),
];
