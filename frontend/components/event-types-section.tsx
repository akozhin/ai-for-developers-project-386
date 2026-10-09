import type { EventType } from "@/lib/api/event-types";

type Props = {
  /** `null` — запрос к API не удался, блок не показываем. */
  eventTypes: EventType[] | null;
};

export function EventTypesSection({ eventTypes }: Props) {
  if (eventTypes === null) return null;

  return (
    <section className="flex w-full max-w-3xl flex-col gap-4">
      <h2 className="text-2xl font-semibold tracking-tight">
        Какие звонки можно заказать
      </h2>
      {eventTypes.length === 0 ? (
        <p className="text-muted-foreground">
          Владелец пока не добавил типы звонков
        </p>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {eventTypes.map((eventType) => (
            <li
              key={eventType.id}
              className="flex flex-col gap-1 rounded-xl border border-border bg-card p-4 text-card-foreground"
            >
              <span className="font-medium">{eventType.title}</span>
              <span className="text-sm text-muted-foreground">
                {eventType.duration_minutes} минут
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
