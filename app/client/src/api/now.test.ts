import {
  afterEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { fetchNow } from "./now";

describe("fetchNow", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("loads the public Now contract", async () => {
    const payload = {
      generatedAt: "2026-07-18T19:00:00.000Z",
      confidence: "high",
      stale: false,
      price: {
        value: 8.42,
        unit: "¢/kWh",
      },
      recommendation: {
        level: "recommended",
        explanationKey: "lower_than_usual",
        actionKey: "run_heavy_appliances",
      },
      contextKey: "lower_than_usual",
    } as const;

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    await expect(fetchNow()).resolves.toEqual(payload);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/now",
      expect.objectContaining({
        headers: {
          Accept: "application/json",
        },
      }),
    );
  });
});
