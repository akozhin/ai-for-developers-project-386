import { cn } from "cn";

import type { Slot } from "@/lib/api/generated";
import { longDateLabel, timeLabel } from "@/lib/booking/time";

export function SlotList({
  date,
  slots,
  timeZone,
  selectedStart,
  onSelect,
}: {
  date: string;
  slots: Slot[];
  timeZone: string;
  selectedStart: string | null;
  onSelect: (startsAt: string) => void;
}) {
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 id="slots-heading" className="font-medium">
          Доступное время
        </h2>
        <p className="text-sm text-muted-foreground">{longDateLabel(date)}</p>
      </div>
      <div
        role="group"
        aria-labelledby="slots-heading"
        className="grid max-h-80 grid-cols-2 gap-2 overflow-y-auto pr-1"
      >
        {slots.map((slot) => (
          <button
            key={slot.starts_at}
            type="button"
            aria-pressed={slot.starts_at === selectedStart}
            onClick={() => onSelect(slot.starts_at)}
            className={cn(
              "rounded-lg border px-3 py-2 text-sm transition-colors",
              slot.starts_at === selectedStart
                ? "border-primary bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted",
            )}
          >
            {timeLabel(slot.starts_at, timeZone)}
          </button>
        ))}
      </div>
    </section>
  );
}
