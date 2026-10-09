import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getEventTypes } from "@/lib/api/event-types";
import { EVENT_TYPES_URL } from "@/mocks/handlers";
import { mockEventTypes } from "@/mocks/event-types";
import { server } from "@/mocks/server";

describe("getEventTypes", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("возвращает типы звонков из ответа API", async () => {
    expect(await getEventTypes()).toEqual(mockEventTypes);
  });

  it("возвращает пустой список, если items пуст", async () => {
    server.use(
      http.get(EVENT_TYPES_URL, () => HttpResponse.json({ items: [] })),
    );

    expect(await getEventTypes()).toEqual([]);
  });

  it("возвращает null и пишет в лог при ответе 500", async () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => undefined);
    server.use(
      http.get(EVENT_TYPES_URL, () => new HttpResponse(null, { status: 500 })),
    );

    expect(await getEventTypes()).toBeNull();
    expect(log).toHaveBeenCalled();
  });

  it("возвращает null при сетевой ошибке", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    server.use(http.get(EVENT_TYPES_URL, () => HttpResponse.error()));

    expect(await getEventTypes()).toBeNull();
  });
});
