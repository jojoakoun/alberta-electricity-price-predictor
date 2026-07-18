jest.mock("../src/repositories/prediction-repository");
jest.mock("../src/utils/explanation");
jest.mock("../src/utils/forecast-time");
jest.mock("../src/utils/freshness");
jest.mock("../src/utils/price");
jest.mock("../src/utils/recommendation");

const repository = require("../src/repositories/prediction-repository");
const explanation = require("../src/utils/explanation");
const forecastTime = require("../src/utils/forecast-time");
const freshness = require("../src/utils/freshness");
const price = require("../src/utils/price");
const recommendation = require("../src/utils/recommendation");

const { getToday } = require("../src/services/today-service");

describe("Today service", () => {
  const viewedAt = new Date("2026-07-18T20:00:00.000Z");

  beforeEach(() => {
    jest.clearAllMocks();

    repository.getLatestPredictions.mockResolvedValue(
      [1, 3, 6, 12, 24].map((horizon, index) => ({
        horizon_hours: horizon,
        target_time_utc: `2026-07-${String(18 + index).padStart(2, "0")}T21:00:00.000Z`,
        predicted_price: String([84.2, 61.4, 72.0, 90.0, 105.0][index]),
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
      })),
    );

    forecastTime.buildForecastTime.mockImplementation(
      (targetTime) => ({
        targetTimeUtc: targetTime,
        targetTimeLocal: "3:00 p.m.",
        temporalWordingKey: "very_soon",
      }),
    );

    price.dollarsPerMwhToCentsPerKwh.mockImplementation(
      (value) => Number(value) / 10,
    );

    recommendation.normalizeRecommendation.mockImplementation(
      (value) => value.toLowerCase(),
    );

    explanation.getExplanationKey.mockReturnValue(
      "lower_than_usual",
    );

    freshness.getFreshness.mockReturnValue({
      confidence: "high",
      stale: false,
    });
  });

  test("builds five public forecasts and selects the lowest price", async () => {
    const today = await getToday(viewedAt);

    expect(today.generatedAt).toBe(
      "2026-07-18T19:00:00.000Z",
    );
    expect(today.confidence).toBe("high");
    expect(today.stale).toBe(false);
    expect(today.forecasts).toHaveLength(5);

    expect(today.forecasts[0]).toEqual({
      horizonHours: 1,
      targetTimeUtc: "2026-07-18T21:00:00.000Z",
      targetTimeLocal: "3:00 p.m.",
      temporalWordingKey: "very_soon",
      priceCents: 8.42,
      recommendation: "acceptable",
      explanationKey: "lower_than_usual",
    });

    expect(today.bestTime).toEqual({
      horizonHours: 3,
      targetTimeUtc: "2026-07-19T21:00:00.000Z",
      targetTimeLocal: "3:00 p.m.",
      priceCents: 6.14,
      recommendation: "recommended",
    });
  });

  test("returns null when no prediction run exists", async () => {
    repository.getLatestPredictions.mockResolvedValue([]);

    await expect(getToday(viewedAt)).resolves.toBeNull();
  });

  test("rejects an incomplete prediction set", async () => {
    repository.getLatestPredictions.mockResolvedValue([
      {
        horizon_hours: 1,
      },
    ]);

    await expect(getToday(viewedAt)).rejects.toThrow(
      "The latest prediction run does not contain the five expected horizons.",
    );
  });
});
