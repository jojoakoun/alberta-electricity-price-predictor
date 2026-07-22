jest.mock("../src/repositories/prediction-repository");
jest.mock("../src/repositories/hourly-price-repository");
jest.mock("../src/utils/explanation");
jest.mock("../src/utils/forecast-time");
jest.mock("../src/utils/freshness");
jest.mock("../src/utils/recommendation");

const predictionRepository = require(
  "../src/repositories/prediction-repository"
);
const hourlyPriceRepository = require(
  "../src/repositories/hourly-price-repository"
);
const explanation = require("../src/utils/explanation");
const forecastTime = require("../src/utils/forecast-time");
const freshness = require("../src/utils/freshness");
const recommendation = require("../src/utils/recommendation");

const { getToday } = require("../src/services/today-service");

const HORIZONS = [1, 3, 6, 12, 24];

const RUN_DETAIL = JSON.stringify({
  schemaVersion: 1,
  forecastKinds: {
    1: "model_forecast",
    3: "model_forecast",
    6: "model_forecast",
    12: "model_forecast",
    24: "persistence_reference",
  },
});

function buildPredictions({
  prices = [84.2, 61.4, 72, 90, 105],
  targets = [
    "2026-07-18T21:00:00.000Z",
    "2026-07-18T23:00:00.000Z",
    "2026-07-19T02:00:00.000Z",
    "2026-07-19T08:00:00.000Z",
    "2026-07-19T20:00:00.000Z",
  ],
  runDetail = RUN_DETAIL,
} = {}) {
  return HORIZONS.map((horizon, index) => ({
    horizon_hours: horizon,
    target_time_utc: targets[index],
    predicted_price: String(prices[index]),
    recommendation: [
      "Acceptable",
      "Recommended",
      "Recommended",
      "Avoid",
      "Avoid",
    ][index],
    explanation:
      "Predicted price is favorable compared with the recent market.",
    generated_at: "2026-07-18T19:00:00.000Z",
    created_at: "2026-07-18T19:07:00.000Z",
    run_detail: runDetail,
  }));
}

describe("Today service", () => {
  const viewedAt = new Date("2026-07-18T20:00:00.000Z");

  beforeEach(() => {
    jest.clearAllMocks();

    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions(),
    );
    hourlyPriceRepository.getLatestFinalizedPrice.mockResolvedValue({
      datetime_utc: "2026-07-18T19:00:00.000Z",
      actual_price: "70.00",
    });

    forecastTime.buildForecastTime.mockImplementation(
      (targetTime) => ({
        targetTimeUtc: targetTime,
        targetTimeLocal: "3:00 p.m.",
        temporalWordingKey: "very_soon",
      }),
    );

    recommendation.normalizeRecommendation.mockImplementation(
      (value) => value.toLowerCase(),
    );

    explanation.getExplanationKey.mockReturnValue(
      "lower_than_usual",
    );

    freshness.getPredictionFreshness.mockReturnValue({
      confidence: "high",
      stale: false,
    });
  });

  test("returns five authentic horizons and a genuine lower-price opportunity", async () => {
    const today = await getToday(viewedAt);

    expect(today).toMatchObject({
      generatedAt: "2026-07-18T19:00:00.000Z",
      confidence: "high",
      stale: false,
      futureForecastStatus: "available",
      comparison: "forecast_lower",
      currentPriceCents: 7,
      currentObservedAtUtc: "2026-07-18T19:00:00.000Z",
      priceDifferenceCents: 0.86,
    });
    expect(today.forecasts).toHaveLength(5);
    expect(
      today.forecasts.map((forecast) => forecast.horizonHours),
    ).toEqual(HORIZONS);
    expect(today.forecasts[0]).toEqual({
      horizonHours: 1,
      targetTimeUtc: "2026-07-18T21:00:00.000Z",
      targetTimeLocal: "3:00 p.m.",
      temporalWordingKey: "very_soon",
      priceCents: 8.42,
      recommendation: "acceptable",
      explanationKey: "lower_than_usual",
      forecastKind: "model_forecast",
    });
    expect(today.bestTime).toEqual({
      horizonHours: 3,
      targetTimeUtc: "2026-07-18T23:00:00.000Z",
      targetTimeLocal: "3:00 p.m.",
      priceCents: 6.14,
      recommendation: "recommended",
    });
    expect(
      freshness.getPredictionFreshness,
    ).toHaveBeenCalledWith(
      "2026-07-18T19:00:00.000Z",
      viewedAt,
    );
  });

  test("treats equality after public rounding as no expected saving", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        prices: [84.2, 61.444, 72, 90, 105],
      }),
    );
    hourlyPriceRepository.getLatestFinalizedPrice.mockResolvedValue({
      datetime_utc: "2026-07-18T19:00:00.000Z",
      actual_price: "61.449",
    });

    const today = await getToday(viewedAt);

    expect(today.comparison).toBe("forecast_equal");
    expect(today.currentPriceCents).toBe(6.14);
    expect(today.bestTime.priceCents).toBe(6.14);
    expect(today.priceDifferenceCents).toBe(0);
  });

  test("reports that the current observed price is lower when every eligible forecast is higher", async () => {
    hourlyPriceRepository.getLatestFinalizedPrice.mockResolvedValue({
      datetime_utc: "2026-07-18T19:00:00.000Z",
      actual_price: "50.00",
    });

    const today = await getToday(viewedAt);

    expect(today.comparison).toBe("current_lower");
    expect(today.currentPriceCents).toBe(5);
    expect(today.priceDifferenceCents).toBe(1.14);
  });

  test("keeps the persistence reference visible but excludes it from best-time selection", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        prices: [84.2, 61.4, 72, 90, 10],
      }),
    );

    const today = await getToday(viewedAt);

    expect(today.bestTime.horizonHours).toBe(3);
    expect(today.forecasts[4]).toMatchObject({
      horizonHours: 24,
      priceCents: 1,
      forecastKind: "persistence_reference",
    });
  });

  test("preserves truthful provenance for existing successful runs", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        prices: [84.2, 61.4, 72, 90, 10],
        runDetail:
          "Application pipeline prediction cycle.",
      }),
    );

    const today = await getToday(viewedAt);

    expect(today.bestTime.horizonHours).toBe(3);
    expect(today.forecasts[4].forecastKind).toBe(
      "persistence_reference",
    );
  });

  test("does not create an opportunity when legacy provenance is unknown", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        runDetail: "Unrecognized legacy run.",
      }),
    );

    const today = await getToday(viewedAt);

    expect(today.futureForecastStatus).toBe(
      "provenance_unavailable",
    );
    expect(today.bestTime).toBeNull();
    expect(today.comparison).toBe("unavailable");
    expect(
      today.forecasts.every(
        (forecast) => forecast.forecastKind === "unknown",
      ),
    ).toBe(true);
  });

  test("rejects corrupt versioned provenance instead of silently falling back", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        runDetail: "{not-json",
      }),
    );

    await expect(getToday(viewedAt)).rejects.toThrow(
      "invalid forecast metadata",
    );
  });

  test("keeps an eligible best time but marks comparison unavailable without an observed price", async () => {
    hourlyPriceRepository.getLatestFinalizedPrice.mockResolvedValue(null);

    const today = await getToday(viewedAt);

    expect(today.bestTime.horizonHours).toBe(3);
    expect(today.futureForecastStatus).toBe("available");
    expect(today.comparison).toBe("unavailable");
    expect(today.currentPriceCents).toBeNull();
    expect(today.currentObservedAtUtc).toBeNull();
    expect(today.priceDifferenceCents).toBeNull();
  });

  test("distinguishes passed targets from forecasts that are not cheaper", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        targets: [
          "2026-07-18T10:00:00.000Z",
          "2026-07-18T11:00:00.000Z",
          "2026-07-18T12:00:00.000Z",
          "2026-07-18T13:00:00.000Z",
          "2026-07-18T14:00:00.000Z",
        ],
      }),
    );

    const today = await getToday(viewedAt);

    expect(today.futureForecastStatus).toBe("none_remaining");
    expect(today.bestTime).toBeNull();
    expect(today.comparison).toBe("unavailable");
    expect(today.confidence).toBe("high");
    expect(today.stale).toBe(false);
  });

  test("does not turn a future persistence reference into an opportunity when model targets passed", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue(
      buildPredictions({
        targets: [
          "2026-07-18T10:00:00.000Z",
          "2026-07-18T11:00:00.000Z",
          "2026-07-18T12:00:00.000Z",
          "2026-07-18T13:00:00.000Z",
          "2026-07-19T20:00:00.000Z",
        ],
      }),
    );

    const today = await getToday(viewedAt);

    expect(today.futureForecastStatus).toBe("reference_only");
    expect(today.bestTime).toBeNull();
    expect(today.comparison).toBe("unavailable");
    expect(today.forecasts).toHaveLength(5);
  });

  test("returns null when no prediction run exists", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue([]);

    await expect(getToday(viewedAt)).resolves.toBeNull();
  });

  test("rejects an incomplete prediction set", async () => {
    predictionRepository.getLatestPredictions.mockResolvedValue([
      {
        horizon_hours: 1,
      },
    ]);

    await expect(getToday(viewedAt)).rejects.toThrow(
      "The latest prediction run does not contain the five expected horizons.",
    );
  });
});
