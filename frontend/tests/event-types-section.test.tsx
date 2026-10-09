import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EventTypesSection } from "@/components/event-types-section";
import { mockEventTypes } from "@/mocks/event-types";

describe("EventTypesSection", () => {
  it("показывает карточки с названием и длительностью", () => {
    render(<EventTypesSection eventTypes={mockEventTypes} />);

    expect(
      screen.getByRole("heading", { name: "Какие звонки можно заказать" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Консультация")).toBeInTheDocument();
    expect(screen.getByText("30 минут")).toBeInTheDocument();
    expect(screen.getByText("Разбор кода")).toBeInTheDocument();
    expect(screen.getByText("60 минут")).toBeInTheDocument();
  });

  it("при пустом списке объясняет, что типов звонков пока нет", () => {
    render(<EventTypesSection eventTypes={[]} />);

    expect(
      screen.getByText("Владелец пока не добавил типы звонков"),
    ).toBeInTheDocument();
  });

  it("при ошибке запроса скрывает блок целиком", () => {
    const { container } = render(<EventTypesSection eventTypes={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});
