export type MonthKey = `${number}-${string}`;

const MONTH_NAMES = [
  "январь",
  "февраль",
  "март",
  "апрель",
  "май",
  "июнь",
  "июль",
  "август",
  "сентябрь",
  "октябрь",
  "ноябрь",
  "декабрь",
];

/** Календарный месяц момента `date` по поясу `timeZone`: «2026-10». */
export function monthKey(date: Date | string, timeZone: string): MonthKey {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
  }).formatToParts(new Date(date));
  const year = parts.find((part) => part.type === "year")?.value ?? "";
  const month = parts.find((part) => part.type === "month")?.value ?? "";
  return `${Number(year)}-${month}`;
}

/** Следующий за `key` месяц. */
export function nextMonthKey(key: MonthKey): MonthKey {
  const [year, month] = key.split("-").map(Number);
  return month === 12
    ? `${year + 1}-01`
    : `${year}-${String(month + 1).padStart(2, "0")}`;
}

/** «Октябрь 2026». */
export function monthTitle(key: MonthKey): string {
  const [year, month] = key.split("-").map(Number);
  const name = MONTH_NAMES[month - 1];
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${year}`;
}
