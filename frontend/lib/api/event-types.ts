import { cacheLife } from "next/cache";

export type EventType = {
  id: string;
  title: string;
  duration_minutes: number;
};

function isEventType(value: unknown): value is EventType {
  if (typeof value !== "object" || value === null) return false;
  const { id, title, duration_minutes } = value as Record<string, unknown>;
  return (
    typeof id === "string" &&
    typeof title === "string" &&
    typeof duration_minutes === "number"
  );
}

function parseItems(body: unknown): EventType[] {
  if (typeof body !== "object" || body === null) {
    throw new Error("Ответ API не объект");
  }
  const { items } = body as Record<string, unknown>;
  if (!Array.isArray(items) || !items.every(isEventType)) {
    throw new Error("Ответ API не соответствует контракту event-types");
  }
  return items;
}

async function fetchEventTypes(): Promise<EventType[]> {
  "use cache";
  cacheLife({ revalidate: 60, stale: 60, expire: 300 });

  const baseUrl = process.env.API_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/v1/event-types`);
  if (!response.ok) {
    throw new Error(`API вернул ${response.status}`);
  }
  return parseItems(await response.json());
}

/**
 * Типы звонков из API (кеш 60 секунд); `null` — запрос не удался,
 * причина в серверном логе. Ошибки в кеш не попадают.
 */
export async function getEventTypes(): Promise<EventType[] | null> {
  try {
    return await fetchEventTypes();
  } catch (error) {
    console.error("Не удалось получить типы звонков", error);
    return null;
  }
}
