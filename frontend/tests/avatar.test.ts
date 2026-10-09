import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("аватар владельца по умолчанию", () => {
  it("лежит в публичных файлах и является JPEG (backend отдаёт на него /avatar.jpg)", () => {
    const avatar = readFileSync(resolve(__dirname, "../public/avatar.jpg"));

    expect([...avatar.subarray(0, 3)]).toEqual([0xff, 0xd8, 0xff]);
  });
});
