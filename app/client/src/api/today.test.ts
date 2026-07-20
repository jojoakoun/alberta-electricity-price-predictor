import {
  afterEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { fetchToday } from "./today";

describe("fetchToday", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("loads the public Today contract", async () => {
    const payload = {
      generatedAt: "2026-07-20T00:00:00.000Z",
      confidence: "high",
      stale: false,
      forecasts: [],
      bestTime: {
        horizonHours: 6,
        targetTimeUtc: "2026-07-20T06:00:00.000Z",
        targetTimeLocal: "12:00 a.m.",
        priceCents: 1.32,
        recommendation: "acceptable",
      },
    } as const;

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    await expect(fetchToday()).resolves.toEqual(payload);
  });
});
