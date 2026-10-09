import { http, HttpResponse } from "msw";

import type { EventTypeList } from "@/lib/api/generated";

import { mockEventTypes } from "./event-types";

export const EVENT_TYPES_URL = "http://localhost:8000/api/v1/event-types";

export const handlers = [
  http.get(EVENT_TYPES_URL, () =>
    HttpResponse.json<EventTypeList>({ items: mockEventTypes }),
  ),
];
