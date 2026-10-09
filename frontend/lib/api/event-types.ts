import { cacheLife } from "next/cache";

import { listEventTypes } from "@/lib/api/generated";
import type { EventType } from "@/lib/api/generated";

export type { EventType };

async function fetchEventTypes(): Promise<EventType[]> {
  "use cache";
  cacheLife({ revalidate: 60, stale: 60, expire: 300 });

  const { data } = await listEventTypes({
    baseUrl: process.env.API_URL ?? "http://localhost:8000",
    throwOnError: true,
  });
  return data.items;
}

/**
 * Типы событий из API (кеш 60 секунд); `null` — запрос не удался,
 * причина в серверном логе. Ошибки в кеш не попадают.
 */
export async function getEventTypes(): Promise<EventType[] | null> {
  try {
    return await fetchEventTypes();
  } catch (error) {
    console.error("Не удалось получить типы событий", error);
    return null;
  }
}
