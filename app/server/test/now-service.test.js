jest.mock("../src/repositories/prediction-repository");
jest.mock("../src/utils/price");
jest.mock("../src/utils/recommendation");
jest.mock("../src/utils/explanation");
jest.mock("../src/utils/freshness");
jest.mock("../src/utils/market-context");
jest.mock("../src/utils/action");

const repository = require("../src/repositories/prediction-repository");
const price = require("../src/utils/price");
const recommendation = require("../src/utils/recommendation");
const explanation = require("../src/utils/explanation");
const freshness = require("../src/utils/freshness");
const marketContext = require("../src/utils/market-context");
const action = require("../src/utils/action");

const { getNow } = require("../src/services/now-service");

describe("Now service", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    repository.getLatestPredictions.mockResolvedValue([
      {
        horizon_hours: 1,
        recommendation: "Recommended",
        explanation:
          "Predicted price is favorable compared with the recent market.",
        generated_at: "2026-07-18T19:00:00.000Z",
      },
    ]);

    repository.getLatestFinalizedPrice.mockResolvedValue({
      actual_price: "84.20",
    });

    repository.getRecentFinalizedPrices.mockResolvedValue([]);

    price.dollarsPerMwhToCentsPerKwh.mockReturnValue(8.42);
    recommendation.normalizeRecommendation.mockReturnValue("recommended");
    explanation.getExplanationKey.mockReturnValue("lower_than_usual");
    freshness.getFreshness.mockReturnValue({
      confidence: "high",
      stale: false,
    });
    marketContext.getMarketContext.mockReturnValue("about_average");
    action.getActionKey.mockReturnValue("run_heavy_appliances");
  });

  test("builds the public Now response", async () => {
    await expect(getNow()).resolves.toEqual({
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
      contextKey: "about_average",
    });
  });
});
