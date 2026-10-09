import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { EventTypesLoader } from "@/components/event-types-loader";
import { EVENT_TYPES_URL } from "@/mocks/handlers";
import { server } from "@/mocks/server";

describe("EventTypesLoader", () => {
  it("показывает типы звонков из API", async () => {
    render(await EventTypesLoader());

    expect(screen.getByText("Консультация")).toBeInTheDocument();
    expect(screen.getByText("Разбор кода")).toBeInTheDocument();
  });

  it("скрывает блок, если API недоступен", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    server.use(
      http.get(EVENT_TYPES_URL, () => new HttpResponse(null, { status: 500 })),
    );

    const { container } = render(await EventTypesLoader());

    expect(container).toBeEmptyDOMElement();
  });
});
