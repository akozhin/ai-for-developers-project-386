import { http, HttpResponse } from "msw";

import type { BookingList, EventTypeList, Profile } from "@/lib/api/generated";

import { mockBookings, mockProfile } from "./bookings";
import { mockEventTypes } from "./event-types";

export const EVENT_TYPES_URL = "http://localhost:3000/api/v1/event-types";

export const BOOKINGS_URL = "http://localhost:3000/api/v1/bookings";
export const PROFILE_URL = "http://localhost:3000/api/v1/profile";

export const handlers = [
  http.get(EVENT_TYPES_URL, () =>
    HttpResponse.json<EventTypeList>({ items: mockEventTypes }),
  ),
  http.get(BOOKINGS_URL, () =>
    HttpResponse.json<BookingList>({ items: mockBookings }),
  ),
  http.get(PROFILE_URL, () => HttpResponse.json<Profile>(mockProfile)),
];
