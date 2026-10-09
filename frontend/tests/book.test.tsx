import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import BookPage from "@/app/book/page";

describe("BookPage", () => {
  it("показывает заглушку и ссылку на главную", () => {
    render(<BookPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Выбор времени" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Назад" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});
