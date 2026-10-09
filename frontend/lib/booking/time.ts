import type { Slot, SlotDay } from "@/lib/api/generated";

const formatters = new Map<string, Intl.DateTimeFormat>();

/** Форматтер с кэшем: создание `Intl.DateTimeFormat` дорого, а вызовов много. */
function cachedFormatter(
  timeZone: string,
  locale: string,
  options: Intl.DateTimeFormatOptions,
): Intl.DateTimeFormat {
  const id = `${locale}|${timeZone}|${JSON.stringify(options)}`;
  let formatter = formatters.get(id);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat(locale, { ...options, timeZone });
    formatters.set(id, formatter);
  }
  return formatter;
}

/** Дата календаря `YYYY-MM-DD` для момента времени в заданном часовом поясе. */
export function dateKey(iso: string, timeZone: string): string {
  const parts = cachedFormatter(timeZone, "en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(iso));
  const part = (type: string) =>
    parts.find((item) => item.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}`;
}

/** Время `ЧЧ:ММ` в заданном часовом поясе. */
export function timeLabel(iso: string, timeZone: string): string {
  return cachedFormatter(timeZone, "ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(iso));
}

function utcDate(key: string): Date {
  return new Date(`${key}T00:00:00Z`);
}

function withoutYearSuffix(text: string): string {
  return text.replace(/\s?г\.$/, "");
}

/** «12 октября» для даты календаря. */
export function dayMonthLabel(key: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: "UTC",
    day: "numeric",
    month: "long",
  }).format(utcDate(key));
}

/** «Понедельник, 12 октября 2026» для даты календаря. */
export function longDateLabel(key: string): string {
  const text = withoutYearSuffix(
    new Intl.DateTimeFormat("ru-RU", {
      timeZone: "UTC",
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(utcDate(key)),
  );
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** «октябрь 2026» для месяца `YYYY-MM`. */
export function monthLabel(month: string): string {
  return withoutYearSuffix(
    new Intl.DateTimeFormat("ru-RU", {
      timeZone: "UTC",
      month: "long",
      year: "numeric",
    }).format(utcDate(`${month}-01`)),
  );
}

/** Ячейки месяца `YYYY-MM` с понедельника; пустые ячейки — `null`. */
export function monthCells(month: string): (string | null)[] {
  const [year, number] = month.split("-").map(Number);
  const firstWeekday =
    (new Date(Date.UTC(year, number - 1, 1)).getUTCDay() + 6) % 7;
  const daysInMonth = new Date(Date.UTC(year, number, 0)).getUTCDate();
  return [
    ...Array<null>(firstWeekday).fill(null),
    ...Array.from(
      { length: daysInMonth },
      (_, index) => `${month}-${String(index + 1).padStart(2, "0")}`,
    ),
  ];
}

/** Сдвиг месяца `YYYY-MM` на `delta` месяцев. */
export function shiftMonth(month: string, delta: number): string {
  const [year, number] = month.split("-").map(Number);
  const shifted = new Date(Date.UTC(year, number - 1 + delta, 1));
  return shifted.toISOString().slice(0, 7);
}

/** Слоты окна, сгруппированные по датам календаря в выбранном часовом поясе. */
export function groupSlotsByDate(
  days: SlotDay[],
  timeZone: string,
): Map<string, Slot[]> {
  const grouped = new Map<string, Slot[]>();
  for (const slot of days.flatMap((day) => day.slots)) {
    const key = dateKey(slot.starts_at, timeZone);
    grouped.set(key, [...(grouped.get(key) ?? []), slot]);
  }
  for (const slots of grouped.values()) {
    slots.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
  }
  return grouped;
}
