import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { BookingScreen } from "@/components/booking/booking-screen";
import type {
  BookingInput,
  EventType,
  EventTypeList,
  Profile,
  SlotsResponse,
} from "@/lib/api/generated";
import {
  API,
  bookingScreenHandlers,
  call30,
  mockProfile,
  slot,
  slotsResponse,
} from "@/mocks/booking-screen";
import { server } from "@/mocks/server";

beforeEach(() => {
  server.use(...bookingScreenHandlers);
});

/** Тексты кнопок слотов выбранного дня. */
async function visibleSlots(): Promise<string[]> {
  const group = await screen.findByRole("group", { name: "Доступное время" });
  return within(group)
    .getAllByRole("button")
    .map((button) => button.textContent ?? "");
}

/** Считает запросы слотов типа события. */
function countSlotRequests(id: string): { count: () => number } {
  let requests = 0;
  server.use(
    http.get(`${API}/event-types/${id}/slots`, () => {
      requests += 1;
      return HttpResponse.json<SlotsResponse>(
        id === "call-30"
          ? bookingScreenHandlersSlots30()
          : bookingScreenHandlersSlots60(),
      );
    }),
  );
  return { count: () => requests };
}

function bookingScreenHandlersSlots30(): SlotsResponse {
  return slotsResponse({
    "2026-10-12": [
      slot("2026-10-12T07:00:00Z", 30),
      slot("2026-10-12T07:30:00Z", 30),
      slot("2026-10-12T08:00:00Z", 30),
    ],
    "2026-10-13": [
      slot("2026-10-13T03:30:00Z", 30),
      slot("2026-10-13T07:00:00Z", 30),
      slot("2026-10-13T07:30:00Z", 30),
    ],
    "2026-10-15": [slot("2026-10-15T09:00:00Z", 30)],
  });
}

function bookingScreenHandlersSlots60(): SlotsResponse {
  return slotsResponse({
    "2026-10-12": [slot("2026-10-12T07:00:00Z", 60)],
    "2026-10-13": [slot("2026-10-13T07:00:00Z", 60)],
  });
}

/** Выбирает слот 10:30 понедельника и заполняет обязательные поля формы. */
async function fillBooking(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: "10:30" }));
  await user.type(screen.getByLabelText(/Ваше имя/), "Анна");
  await user.type(
    screen.getByLabelText(/Электронная почта/),
    "anna@example.com",
  );
}

describe("главный экран записи", () => {
  it("показывает профиль, типы событий, календарь и слоты ближайшего дня", async () => {
    render(<BookingScreen guestTimeZone="America/New_York" />);

    expect(await screen.findByText("Alexandr Kozhin")).toBeInTheDocument();
    expect(screen.getByText(/Видеозвонок/)).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Alexandr Kozhin" }),
    ).toHaveAttribute("src", "/avatar.jpg");
    const types = screen.getByRole("radiogroup", { name: "Тип события" });
    expect(
      within(types).getByRole("radio", { name: /Консультация/ }),
    ).toBeChecked();
    expect(
      within(types).getByRole("radio", { name: /Разбор кода/ }),
    ).not.toBeChecked();
    expect(
      screen.getByText("Короткий созвон: знакомство или быстрый вопрос"),
    ).toBeInTheDocument();
    expect(await screen.findByText("октябрь 2026")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /^12 октября/ }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(await visibleSlots()).toEqual(["10:00", "10:30", "11:00"]);
  });

  it("переключение типа события загружает его слоты и описание", async () => {
    const user = userEvent.setup();
    render(<BookingScreen guestTimeZone="America/New_York" />);
    await visibleSlots();

    await user.click(screen.getByRole("radio", { name: /Разбор кода/ }));

    expect(
      await screen.findByText("Подробный разбор задачи или проекта"),
    ).toBeInTheDocument();
    await waitFor(async () => expect(await visibleSlots()).toEqual(["10:00"]));
    expect(screen.getByRole("button", { name: /^15 октября/ })).toBeDisabled();
  });

  it("дни без слотов недоступны, выбор дня показывает его слоты", async () => {
    const user = userEvent.setup();
    render(<BookingScreen guestTimeZone="America/New_York" />);
    await visibleSlots();

    expect(
      screen.getByRole("button", {
        name: /^14 октября, нет свободного времени/,
      }),
    ).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /^13 октября/ }));

    expect(await visibleSlots()).toEqual(["06:30", "10:00", "10:30"]);
    expect(screen.getByRole("button", { name: /^13 октября/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("форма активна только при выбранном слоте, имени и корректной почте", async () => {
    const user = userEvent.setup();
    render(<BookingScreen guestTimeZone="America/New_York" />);
    const submit = await screen.findByRole("button", { name: "Забронировать" });
    expect(submit).toBeDisabled();
    expect(
      screen.getByText("Выберите дату и время, чтобы продолжить."),
    ).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: "10:30" }));
    const summary = screen.getByRole("list", { name: "Выбранная встреча" });
    expect(
      within(summary).getByText(/Понедельник, 12 октября 2026 · 10:30–11:00/),
    ).toBeInTheDocument();
    expect(within(summary).getByText("30 мин")).toBeInTheDocument();
    expect(submit).toBeDisabled();

    await user.type(screen.getByLabelText(/Ваше имя/), "Анна");
    await user.type(screen.getByLabelText(/Электронная почта/), "не-почта");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Укажите корректный адрес электронной почты",
    );
    expect(submit).toBeDisabled();

    await user.clear(screen.getByLabelText(/Электронная почта/));
    await user.type(
      screen.getByLabelText(/Электронная почта/),
      "anna@example.com",
    );
    expect(submit).toBeEnabled();
  });

  it("успешное бронирование: тело запроса, подтверждение, «Забронировать ещё» и перезагрузка слотов", async () => {
    const user = userEvent.setup();
    const slotRequests = countSlotRequests("call-30");
    let sent: BookingInput | null = null;
    server.use(
      http.post(`${API}/bookings`, async ({ request }) => {
        sent = (await request.json()) as BookingInput;
        return HttpResponse.json(
          {
            id: "0b8f6e1c-5f0a-4c53-9d7e-2d4e6f8a1b3c",
            event_type: call30,
            starts_at: sent.starts_at,
            ends_at: "2026-10-12T08:00:00Z",
            guest_name: sent.guest_name,
            guest_email: sent.guest_email,
            comment: sent.comment,
            created_at: "2026-10-12T06:00:00Z",
          },
          { status: 201 },
        );
      }),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);
    await fillBooking(user);
    await user.type(
      screen.getByLabelText(/Комментарий/),
      "Хочу обсудить проект",
    );
    expect(slotRequests.count()).toBe(1);

    await user.click(screen.getByRole("button", { name: "Забронировать" }));

    expect(
      await screen.findByRole("heading", { name: "Встреча забронирована" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Понедельник, 12 октября 2026 · 10:30–11:00/),
    ).toBeInTheDocument();
    expect(sent).toEqual({
      event_type_id: "call-30",
      starts_at: "2026-10-12T07:30:00Z",
      guest_name: "Анна",
      guest_email: "anna@example.com",
      comment: "Хочу обсудить проект",
    });
    await waitFor(() => expect(slotRequests.count()).toBe(2));

    await user.click(screen.getByRole("button", { name: "Забронировать ещё" }));

    expect(
      screen.getByRole("heading", { name: "Подтвердить встречу" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Комментарий/)).toHaveValue("");
    expect(
      screen.getByRole("button", { name: "Забронировать" }),
    ).toBeDisabled();
  });

  it.each([
    ["slot_taken", "Слот только что заняли"],
    ["slot_not_available", "Время недоступно, выберите другое"],
  ])(
    "ошибка %s показывает сообщение и перезагружает слоты",
    async (code, message) => {
      const user = userEvent.setup();
      const slotRequests = countSlotRequests("call-30");
      server.use(
        http.post(`${API}/bookings`, () =>
          HttpResponse.json(
            { code, message: "служебный текст" },
            { status: 409 },
          ),
        ),
      );
      render(<BookingScreen guestTimeZone="America/New_York" />);
      await fillBooking(user);

      await user.click(screen.getByRole("button", { name: "Забронировать" }));

      expect(await screen.findByText(message)).toBeInTheDocument();
      await waitFor(() => expect(slotRequests.count()).toBe(2));
      expect(
        screen.getByText("Выберите дату и время, чтобы продолжить."),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", { name: "Встреча забронирована" }),
      ).not.toBeInTheDocument();
    },
  );

  it("неожиданная ошибка сервера показывает общее сообщение", async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        `${API}/bookings`,
        () => new HttpResponse(null, { status: 500 }),
      ),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);
    await fillBooking(user);

    await user.click(screen.getByRole("button", { name: "Забронировать" }));

    expect(
      await screen.findByText("Не удалось забронировать, попробуйте ещё раз"),
    ).toBeInTheDocument();
  });

  it("переключение пояса пересчитывает время и группировку по дням", async () => {
    const user = userEvent.setup();
    render(<BookingScreen guestTimeZone="America/New_York" />);
    expect(await visibleSlots()).toEqual(["10:00", "10:30", "11:00"]);

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Часовой пояс" }),
      "America/New_York (ваш пояс)",
    );

    // 07:00Z = 03:00 по Нью-Йорку, а слот вторника 03:30Z (06:30 МСК) попадает на вечер понедельника.
    expect(await visibleSlots()).toEqual(["03:00", "03:30", "04:00", "23:30"]);
    expect(
      screen.getByText(/Видеозвонок · America\/New_York/),
    ).toBeInTheDocument();
  });

  it("без аватара показываются инициалы", async () => {
    server.use(
      http.get(`${API}/profile`, () =>
        HttpResponse.json<Profile>({ ...mockProfile, avatar_url: null }),
      ),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);

    expect(await screen.findByText("AK")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("пустые состояния: нет типов событий и нет свободного времени", async () => {
    server.use(
      http.get(`${API}/event-types`, () =>
        HttpResponse.json<EventTypeList>({ items: [] }),
      ),
    );
    const { unmount } = render(
      <BookingScreen guestTimeZone="America/New_York" />,
    );
    expect(
      await screen.findByText("Пока нет доступных типов событий."),
    ).toBeInTheDocument();
    unmount();

    server.use(
      http.get(`${API}/event-types`, () =>
        HttpResponse.json<EventTypeList>({ items: [call30] }),
      ),
      http.get(`${API}/event-types/call-30/slots`, () =>
        HttpResponse.json<SlotsResponse>(slotsResponse({})),
      ),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);
    expect(
      await screen.findByText("В ближайшие 14 дней свободного времени нет."),
    ).toBeInTheDocument();
  });

  it("при ошибке загрузки показывает сообщение и повторяет запрос по кнопке", async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${API}/profile`, () => new HttpResponse(null, { status: 500 })),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);
    expect(
      await screen.findByText(/Не удалось загрузить данные/),
    ).toBeInTheDocument();

    server.use(...bookingScreenHandlers);
    await user.click(screen.getByRole("button", { name: "Повторить" }));

    expect(await screen.findByText("Alexandr Kozhin")).toBeInTheDocument();
  });

  it("окно на границе месяцев: стрелки переключают месяц, дни следующего месяца доступны", async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${API}/event-types/call-30/slots`, () =>
        HttpResponse.json<SlotsResponse>(
          slotsResponse(
            {
              "2026-10-26": [slot("2026-10-26T07:00:00Z", 30)],
              "2026-11-03": [slot("2026-11-03T07:00:00Z", 30)],
            },
            "2026-10-25",
          ),
        ),
      ),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);
    expect(await screen.findByText("октябрь 2026")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Предыдущий месяц" }),
    ).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Следующий месяц" }));

    expect(screen.getByText("ноябрь 2026")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Следующий месяц" }),
    ).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /^3 ноября/ }));
    expect(await visibleSlots()).toEqual(["10:00"]);
  });

  it("при многих типах события показывает выпадающий список", async () => {
    const many: EventType[] = Array.from({ length: 5 }, (_, index) => ({
      ...call30,
      id: `call-${index + 1}`,
      title: `Тип ${index + 1}`,
    }));
    server.use(
      http.get(`${API}/event-types`, () =>
        HttpResponse.json<EventTypeList>({ items: many }),
      ),
      http.get(`${API}/event-types/call-1/slots`, () =>
        HttpResponse.json<SlotsResponse>(slotsResponse({})),
      ),
    );
    render(<BookingScreen guestTimeZone="America/New_York" />);

    const select = await screen.findByRole("combobox", { name: "Тип события" });
    expect(within(select).getAllByRole("option")).toHaveLength(5);
  });
});
