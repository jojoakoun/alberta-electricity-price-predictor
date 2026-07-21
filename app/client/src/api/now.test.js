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
    };

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

  test("rejects a non-finite observed price with its field name", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        generatedAt: "2026-07-18T19:00:00.000Z",
        confidence: "high",
        stale: false,
        price: {
          value: null,
          unit: "¢/kWh",
        },
        recommendation: {
          level: "recommended",
          explanationKey: "lower_than_usual",
          actionKey: "run_heavy_appliances",
        },
        contextKey: "lower_than_usual",
      })),
    );

    await expect(fetchNow()).rejects.toThrow(
      "price.value must be a finite number",
    );
  });

  test("rejects a malformed optional observation timestamp", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        generatedAt: "2026-07-18T19:00:00.000Z",
        confidence: "high",
        stale: false,
        price: {
          value: 8.42,
          unit: "¢/kWh",
          observedAtUtc: "not-a-timestamp",
        },
        recommendation: {
          level: "recommended",
          explanationKey: "lower_than_usual",
          actionKey: "run_heavy_appliances",
        },
        contextKey: "lower_than_usual",
      })),
    );

    await expect(fetchNow()).rejects.toThrow(
      "price.observedAtUtc must be a valid timestamp",
    );
  });

  test("rejects a UTC field without an explicit timezone", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        generatedAt: "2026-07-18T19:00:00",
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
      })),
    );

    await expect(fetchNow()).rejects.toThrow(
      "generatedAt must be a valid timestamp with an explicit timezone",
    );
  });
});
