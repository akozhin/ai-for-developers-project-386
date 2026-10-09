import { client } from "@/lib/api/generated/client.gen";

/**
 * Адрес API для SDK. В браузере пусто: запросы идут на тот же origin (`/api/...`),
 * а Next.js проксирует их на backend (см. `rewrites` в `next.config.ts`).
 * В тестах задаётся через `NEXT_PUBLIC_API_BASE_URL`: у Node-fetch нет текущего origin.
 */
client.setConfig({ baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "" });

export { client };
