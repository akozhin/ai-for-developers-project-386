import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "@/app/page";

describe("Home", () => {
  it("показывает заголовок сервиса", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Запись на звонок" }),
    ).toBeInTheDocument();
  });

  it("ведёт ссылкой «Записаться» на страницу записи", () => {
    render(<Home />);

    expect(screen.getByRole("link", { name: "Записаться" })).toHaveAttribute(
      "href",
      "/book",
    );
  });

  it("рассказывает, как это работает, в три шага", () => {
    render(<Home />);

    const steps = screen.getByRole("list", { name: "Как это работает" });
    expect(steps.querySelectorAll("li")).toHaveLength(3);
  });
});
