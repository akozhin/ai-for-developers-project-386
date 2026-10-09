import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

vi.mock("next/cache", () => ({ cacheLife: vi.fn() }));
vi.mock("next/server", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/server")>()),
  connection: vi.fn(() => Promise.resolve()),
}));

import { server } from "@/mocks/server";

beforeAll(() => {
  process.env.API_URL = "http://localhost:8000";
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
  server.listen({ onUnhandledRequest: "error" });
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => {
  server.close();
});
