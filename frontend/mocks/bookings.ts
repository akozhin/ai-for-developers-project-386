import type { Booking, Profile } from "@/lib/api/generated";

import { mockEventTypes } from "./event-types";

/** «Сейчас» в тестах админки: 9 октября 2026, пояс владельца — Москва. */
export const MOCK_NOW = "2026-10-09T09:00:00Z";

export const mockProfile: Profile = {
  name: "Александр Кожин",
  timezone: "Europe/Moscow",
  avatar_url: null,
  ai_enabled: false,
};

export const mockBookings: Booking[] = [
  {
    id: "b1",
    event_type: mockEventTypes[0],
    starts_at: "2026-10-12T07:00:00Z",
    ends_at: "2026-10-12T07:30:00Z",
    guest_name: "Анна Петрова",
    guest_email: "anna@example.com",
    comment: "Хочу обсудить резюме",
    created_at: "2026-10-08T10:00:00Z",
  },
  {
    id: "b2",
    event_type: mockEventTypes[1],
    starts_at: "2026-10-20T11:00:00Z",
    ends_at: "2026-10-20T12:00:00Z",
    guest_name: "Борис Иванов",
    guest_email: "boris@example.com",
    created_at: "2026-10-08T11:00:00Z",
  },
  {
    // 01:00 1 ноября по Москве, хотя в UTC ещё октябрь
    id: "b3",
    event_type: mockEventTypes[0],
    starts_at: "2026-10-31T22:00:00Z",
    ends_at: "2026-10-31T22:30:00Z",
    guest_name: "Вера Смирнова",
    guest_email: "vera@example.com",
    created_at: "2026-10-08T12:00:00Z",
  },
];
