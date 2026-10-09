import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "cn";

import { dayMonthLabel, monthCells, monthLabel } from "@/lib/booking/time";

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function Calendar({
  month,
  enabledDates,
  selectedDate,
  canGoBack,
  canGoForward,
  onSelectDate,
  onShiftMonth,
}: {
  month: string;
  enabledDates: ReadonlySet<string>;
  selectedDate: string | null;
  canGoBack: boolean;
  canGoForward: boolean;
  onSelectDate: (date: string) => void;
  onShiftMonth: (delta: number) => void;
}) {
  return (
    <section aria-label="Календарь" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <button
          type="button"
          aria-label="Предыдущий месяц"
          disabled={!canGoBack}
          onClick={() => onShiftMonth(-1)}
          className="rounded-md p-1 hover:bg-muted disabled:opacity-30"
        >
          <ChevronLeft className="size-5" />
        </button>
        <p className="font-medium">{monthLabel(month)}</p>
        <button
          type="button"
          aria-label="Следующий месяц"
          disabled={!canGoForward}
          onClick={() => onShiftMonth(1)}
          className="rounded-md p-1 hover:bg-muted disabled:opacity-30"
        >
          <ChevronRight className="size-5" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-muted-foreground">
        {WEEKDAYS.map((weekday) => (
          <span key={weekday}>{weekday}</span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {monthCells(month).map((date, index) =>
          date === null ? (
            <span key={`empty-${index}`} />
          ) : (
            <button
              key={date}
              type="button"
              disabled={!enabledDates.has(date)}
              aria-pressed={date === selectedDate}
              aria-label={`${dayMonthLabel(date)}${enabledDates.has(date) ? "" : ", нет свободного времени"}`}
              onClick={() => onSelectDate(date)}
              className={cn(
                "aspect-square rounded-lg text-sm transition-colors disabled:cursor-not-allowed disabled:text-muted-foreground/40",
                date === selectedDate
                  ? "bg-primary font-semibold text-primary-foreground"
                  : enabledDates.has(date) &&
                      "border bg-background hover:bg-muted",
              )}
            >
              {Number(date.slice(8))}
            </button>
          ),
        )}
      </div>
    </section>
  );
}
