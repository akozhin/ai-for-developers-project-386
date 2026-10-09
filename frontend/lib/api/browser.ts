/**
 * Общие параметры запросов из браузера. По умолчанию адрес пустой: запросы
 * идут на тот же origin и проксируются Next (`rewrites` в `next.config.ts`),
 * поэтому CORS на backend не нужен.
 */
export function browserApi() {
  return { baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "" };
}
