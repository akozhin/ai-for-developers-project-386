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
});
