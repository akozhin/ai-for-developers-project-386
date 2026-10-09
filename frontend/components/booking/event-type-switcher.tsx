import { cn } from "cn";

import type { EventType } from "@/lib/api/generated";

/** Типов больше этого числа — вместо кнопок показываем выпадающий список. */
const MAX_BUTTONS = 4;

export function EventTypeSwitcher({
  eventTypes,
  selectedId,
  onSelect,
}: {
  eventTypes: EventType[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const selected = eventTypes.find((type) => type.id === selectedId);

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-medium">Выберите тип события</h2>
      {eventTypes.length > MAX_BUTTONS ? (
        <select
          aria-label="Тип события"
          value={selectedId}
          onChange={(event) => onSelect(event.target.value)}
          className="h-9 rounded-lg border border-input bg-background px-2 text-sm"
        >
          {eventTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.title} · {type.duration_minutes} мин
            </option>
          ))}
        </select>
      ) : (
        <div
          role="radiogroup"
          aria-label="Тип события"
          className="grid gap-2 sm:grid-cols-2"
        >
          {eventTypes.map((type) => (
            <label
              key={type.id}
              className={cn(
                "flex cursor-pointer flex-col rounded-lg border px-3 py-2 text-sm transition-colors has-focus-visible:ring-3 has-focus-visible:ring-ring/50",
                type.id === selectedId
                  ? "border-primary bg-primary text-primary-foreground"
                  : "bg-background hover:bg-muted",
              )}
            >
              <input
                type="radio"
                name="event-type"
                value={type.id}
                checked={type.id === selectedId}
                onChange={() => onSelect(type.id)}
                className="sr-only"
              />
              <span className="font-medium">{type.title}</span>
              <span className="opacity-80">{type.duration_minutes} мин</span>
            </label>
          ))}
        </div>
      )}
      {selected ? (
        <p className="text-sm text-muted-foreground">{selected.description}</p>
      ) : null}
    </section>
  );
}
