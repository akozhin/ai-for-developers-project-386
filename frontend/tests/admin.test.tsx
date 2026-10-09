import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AdminPage from "@/app/admin/page";
import type { EventType } from "@/lib/api/generated";
import { MOCK_NOW } from "@/mocks/bookings";
import { BOOKINGS_URL, EVENT_TYPES_URL } from "@/mocks/handlers";
import { server } from "@/mocks/server";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(MOCK_NOW) });
});
afterEach(() => {
  vi.useRealTimers();
});

describe("вкладка «Встречи»", () => {
  it("показывает встречи текущего месяца с плашками", async () => {
    render(<AdminPage />);

    expect(
      await screen.findByRole("heading", { name: "Октябрь 2026" }),
    ).toBeInTheDocument();
    const cards = screen.getAllByRole("listitem");
    expect(cards).toHaveLength(2);

    const first = within(cards[0]);
    expect(first.getByText("Консультация")).toBeInTheDocument();
    expect(first.getByText("Анна Петрова")).toBeInTheDocument();
    expect(first.getByText("anna@example.com")).toBeInTheDocument();
    expect(first.getByText("Хочу обсудить резюме")).toBeInTheDocument();
    // 07:00 UTC = 10:00 по Москве
    expect(first.getByText(/10:00/)).toBeInTheDocument();
    expect(first.getByText(/12 октября/)).toBeInTheDocument();
    // порядок по возрастанию
    expect(within(cards[1]).getByText("Борис Иванов")).toBeInTheDocument();
  });

  it("переключает на следующий месяц по поясу владельца", async () => {
    const user = userEvent.setup();
    render(<AdminPage />);
    await screen.findByRole("heading", { name: "Октябрь 2026" });

    await user.click(screen.getByRole("button", { name: "Следующий месяц" }));

    expect(
      screen.getByRole("heading", { name: "Ноябрь 2026" }),
    ).toBeInTheDocument();
    // 22:00 UTC 31 октября — это уже 1 ноября в Москве
    expect(screen.getByText("Вера Смирнова")).toBeInTheDocument();
    expect(screen.queryByText("Анна Петрова")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Текущий месяц" }));
    expect(screen.getByText("Анна Петрова")).toBeInTheDocument();
  });

  it("показывает пустое состояние", async () => {
    server.use(http.get(BOOKINGS_URL, () => HttpResponse.json({ items: [] })));
    render(<AdminPage />);

    expect(
      await screen.findByText("В этом месяце встреч нет"),
    ).toBeInTheDocument();
  });

  it("показывает состояние загрузки", () => {
    render(<AdminPage />);

    expect(screen.getByText("Загрузка…")).toBeInTheDocument();
  });

  it("показывает ошибку загрузки", async () => {
    server.use(
      http.get(BOOKINGS_URL, () => new HttpResponse(null, { status: 500 })),
    );
    render(<AdminPage />);

    expect(
      await screen.findByText("Не удалось загрузить встречи"),
    ).toBeInTheDocument();
  });
});

describe("вкладка «Типы событий»", () => {
  async function openTab() {
    const user = userEvent.setup();
    render(<AdminPage />);
    await user.click(screen.getByRole("tab", { name: "Типы событий" }));
    return user;
  }

  async function fillForm(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText("Идентификатор"), "call-15");
    await user.type(screen.getByLabelText("Название"), "Быстрый вопрос");
    await user.type(screen.getByLabelText("Описание"), "Пятнадцать минут");
    await user.clear(screen.getByLabelText("Длительность, минут"));
    await user.type(screen.getByLabelText("Длительность, минут"), "15");
  }

  it("показывает список типов", async () => {
    await openTab();

    expect(await screen.findByText("Консультация")).toBeInTheDocument();
    expect(screen.getByText("Разбор кода")).toBeInTheDocument();
  });

  it("показывает пустое состояние", async () => {
    server.use(
      http.get(EVENT_TYPES_URL, () => HttpResponse.json({ items: [] })),
    );
    await openTab();

    expect(
      await screen.findByText("Типов событий пока нет"),
    ).toBeInTheDocument();
  });

  it("показывает ошибку загрузки", async () => {
    server.use(
      http.get(EVENT_TYPES_URL, () => new HttpResponse(null, { status: 500 })),
    );
    await openTab();

    expect(
      await screen.findByText("Не удалось загрузить типы событий"),
    ).toBeInTheDocument();
  });

  it("создаёт тип и показывает его в списке", async () => {
    const created: EventType[] = [];
    server.use(
      http.post(EVENT_TYPES_URL, async ({ request }) => {
        const body = (await request.json()) as EventType;
        created.push(body);
        return HttpResponse.json(body, { status: 201 });
      }),
    );
    const user = await openTab();
    await screen.findByText("Консультация");
    server.use(
      http.get(EVENT_TYPES_URL, () =>
        HttpResponse.json({
          items: [
            {
              id: "call-15",
              title: "Быстрый вопрос",
              description: "Пятнадцать минут",
              duration_minutes: 15,
            },
          ],
        }),
      ),
    );

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Создать" }));

    expect(await screen.findByText("Быстрый вопрос")).toBeInTheDocument();
    expect(created).toEqual([
      {
        id: "call-15",
        title: "Быстрый вопрос",
        description: "Пятнадцать минут",
        duration_minutes: 15,
      },
    ]);
    expect(screen.getByLabelText("Идентификатор")).toHaveValue("");
  });

  it("показывает ошибку дубликата id", async () => {
    server.use(
      http.post(EVENT_TYPES_URL, () =>
        HttpResponse.json(
          { code: "event_type_exists", message: "Тип с таким id уже есть" },
          { status: 409 },
        ),
      ),
    );
    const user = await openTab();
    await screen.findByText("Консультация");

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Создать" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Тип с таким id уже есть",
    );
    expect(screen.getByLabelText("Идентификатор")).toHaveValue("call-15");
  });

  it("показывает ошибки валидации у полей", async () => {
    server.use(
      http.post(EVENT_TYPES_URL, () =>
        HttpResponse.json(
          {
            code: "validation_error",
            message: "Ошибка валидации",
            fields: [
              { field: "id", message: "Только строчные буквы и дефис" },
              { field: "duration_minutes", message: "Должно быть больше 0" },
            ],
          },
          { status: 422 },
        ),
      ),
    );
    const user = await openTab();
    await screen.findByText("Консультация");

    await fillForm(user);
    await user.click(screen.getByRole("button", { name: "Создать" }));

    expect(
      await screen.findByText("Только строчные буквы и дефис"),
    ).toBeInTheDocument();
    expect(screen.getByText("Должно быть больше 0")).toBeInTheDocument();
  });
});
