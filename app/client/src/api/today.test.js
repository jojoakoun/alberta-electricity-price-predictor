import {
  afterEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { fetchToday } from "./today";

const forecasts = [
  [1, "2026-07-20T01:00:00.000Z", 2.36, "model_forecast"],
  [3, "2026-07-20T03:00:00.000Z", 2.8, "model_forecast"],
  [6, "2026-07-20T06:00:00.000Z", 1.32, "model_forecast"],
  [12, "2026-07-20T12:00:00.000Z", 1.42, "model_forecast"],
  [24, "2026-07-21T00:00:00.000Z", 1.91, "persistence_reference"],
].map(([
  horizonHours,
  targetTimeUtc,
  priceCents,
  forecastKind,
]) => ({
  horizonHours,
  targetTimeUtc,
  targetTimeLocal: "12:00 a.m.",
  temporalWordingKey: "in_a_few_hours",
  priceCents,
  recommendation: "acceptable",
  explanationKey: "acceptable_market_risk",
  forecastKind,
}));

function buildTodayPayload(overrides = {}) {
  return {
    generatedAt: "2026-07-20T00:00:00.000Z",
    confidence: "high",
    stale: false,
    futureForecastStatus: "available",
    comparison: "forecast_lower",
    currentPriceCents: 2.1,
    currentObservedAtUtc: "2026-07-19T23:00:00.000Z",
    priceDifferenceCents: 0.78,
    forecasts: forecasts.map((forecast) => ({ ...forecast })),
    bestTime: {
      horizonHours: 6,
      targetTimeUtc: "2026-07-20T06:00:00.000Z",
      targetTimeLocal: "12:00 a.m.",
      priceCents: 1.32,
      recommendation: "acceptable",
    },
    ...overrides,
  };
}

function mockTodayPayload(payload) {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    }),
  );
}

describe("fetchToday", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("loads the public Today contract", async () => {
    const payload = buildTodayPayload();
    mockTodayPayload(payload);

    await expect(fetchToday()).resolves.toEqual(payload);
  });

  test("rejects duplicate forecast horizons with the contract field", async () => {
    const payload = buildTodayPayload();
    payload.forecasts[1].horizonHours = 1;
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "forecasts[].horizonHours must equal 1, 3, 6, 12, and 24 in order",
    );
  });

  test("rejects unsupported forecast provenance", async () => {
    const payload = buildTodayPayload();
    payload.forecasts[2].forecastKind = "baseline";
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "forecasts[2].forecastKind contains an unsupported value",
    );
  });

  test("rejects a persistence reference promoted as best time", async () => {
    const payload = buildTodayPayload({
      bestTime: {
        horizonHours: 24,
        targetTimeUtc: "2026-07-21T00:00:00.000Z",
        targetTimeLocal: "12:00 a.m.",
        priceCents: 1.91,
        recommendation: "acceptable",
      },
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "bestTime must reference a model_forecast",
    );
  });

  test("rejects a malformed nullable observation timestamp", async () => {
    const payload = buildTodayPayload({
      currentObservedAtUtc: "not-a-timestamp",
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "currentObservedAtUtc must be a valid timestamp",
    );
  });

  test("rejects incomplete evidence for a lower-price comparison", async () => {
    const payload = buildTodayPayload({
      priceDifferenceCents: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "priceDifferenceCents is required when comparison is forecast_lower",
    );
  });

  test("requires an exact zero difference for an equal comparison", async () => {
    const payload = buildTodayPayload({
      comparison: "forecast_equal",
      priceDifferenceCents: 0.01,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "priceDifferenceCents must equal zero when comparison is forecast_equal",
    );
  });

  test("rejects a difference when the comparison is unavailable", async () => {
    const payload = buildTodayPayload({
      comparison: "unavailable",
      currentPriceCents: null,
      currentObservedAtUtc: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "priceDifferenceCents must be null when comparison is unavailable",
    );
  });

  test("requires observed price and timestamp to remain an atomic pair", async () => {
    const payload = buildTodayPayload({
      comparison: "unavailable",
      currentObservedAtUtc: null,
      priceDifferenceCents: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "currentPriceCents and currentObservedAtUtc must be present or null together",
    );
  });

  test("rejects a comparison when no eligible forecast remains", async () => {
    const payload = buildTodayPayload({
      futureForecastStatus: "none_remaining",
      comparison: "forecast_equal",
      priceDifferenceCents: 0,
      bestTime: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "comparison must reflect eligible forecast and observed-price evidence",
    );
  });

  test("requires a comparison when both forecast and observation exist", async () => {
    const payload = buildTodayPayload({
      comparison: "unavailable",
      priceDifferenceCents: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "comparison must reflect eligible forecast and observed-price evidence",
    );
  });

  test("rejects a best time when the server reports no eligible forecast", async () => {
    const payload = buildTodayPayload({
      futureForecastStatus: "none_remaining",
      comparison: "unavailable",
      currentPriceCents: null,
      currentObservedAtUtc: null,
      priceDifferenceCents: null,
    });
    mockTodayPayload(payload);

    await expect(fetchToday()).rejects.toThrow(
      "bestTime must be null when no eligible future model forecast is available",
    );
  });
});
