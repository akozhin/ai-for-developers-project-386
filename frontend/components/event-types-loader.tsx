import { connection } from "next/server";

import { EventTypesSection } from "@/components/event-types-section";
import { getEventTypes } from "@/lib/api/event-types";

/** Запрашивает типы звонков во время запроса, а не при сборке. */
export async function EventTypesLoader() {
  await connection();
  return <EventTypesSection eventTypes={await getEventTypes()} />;
}
