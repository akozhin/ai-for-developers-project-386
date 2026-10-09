"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import "@/lib/api/client";
import { getProfile, listBookings } from "@/lib/api/generated";
import type { Booking } from "@/lib/api/generated";
import { monthKey, monthTitle, nextMonthKey } from "@/lib/months";

type State =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; bookings: Booking[]; timeZone: string };

type Period = "current" | "next";

export function BookingsTab() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [period, setPeriod] = useState<Period>("current");

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listBookings({ throwOnError: true }),
      getProfile({ throwOnError: true }),
    ])
      .then(([bookings, profile]) => {
        if (cancelled) return;
        setState({
          status: "ready",
          bookings: bookings.data.items,
          timeZone: profile.data.timezone,
        });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return <p className="text-muted-foreground">Загрузка…</p>;
  }
  if (state.status === "error") {
    return (
      <p role="alert" className="text-destructive">
        Не удалось загрузить встречи
      </p>
    );
  }

  const { bookings, timeZone } = state;
  const currentMonth = monthKey(new Date(), timeZone);
  const month =
    period === "current" ? currentMonth : nextMonthKey(currentMonth);
  const visible = bookings
    .filter((booking) => monthKey(booking.starts_at, timeZone) === month)
    .toSorted((a, b) => a.starts_at.localeCompare(b.starts_at));

  const dateFormat = new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    day: "numeric",
    month: "long",
    weekday: "short",
  });
  const timeFormat = new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-2xl font-semibold tracking-tight">
          {monthTitle(month)}
        </h2>
        <div className="flex gap-2">
          <Button
            variant={period === "current" ? "default" : "outline"}
            aria-pressed={period === "current"}
            onClick={() => setPeriod("current")}
          >
            Текущий месяц
          </Button>
          <Button
            variant={period === "next" ? "default" : "outline"}
            aria-pressed={period === "next"}
            onClick={() => setPeriod("next")}
          >
            Следующий месяц
          </Button>
        </div>
      </div>
      {visible.length === 0 ? (
        <p className="text-muted-foreground">В этом месяце встреч нет</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {visible.map((booking) => (
            <li
              key={booking.id}
              className="flex flex-col gap-1 rounded-xl border border-border bg-card p-4 text-card-foreground"
            >
              <span className="text-sm text-muted-foreground">
                {dateFormat.format(new Date(booking.starts_at))},{" "}
                {timeFormat.format(new Date(booking.starts_at))}–
                {timeFormat.format(new Date(booking.ends_at))}
              </span>
              <span className="font-medium">{booking.event_type.title}</span>
              <span>{booking.guest_name}</span>
              <span className="text-sm text-muted-foreground">
                {booking.guest_email}
              </span>
              {booking.comment ? (
                <span className="text-sm">{booking.comment}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
