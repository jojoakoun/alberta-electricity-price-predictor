jest.mock(
  "../src/repositories/prediction-repository"
);

jest.mock("../src/utils/price");
jest.mock("../src/utils/freshness");
jest.mock("../src/utils/market-context");
jest.mock("../src/utils/action");

const repository = require(
  "../src/repositories/prediction-repository"
);

const price = require(
  "../src/utils/price"
);

const freshness = require(
  "../src/utils/freshness"
);

const marketContext = require(
  "../src/utils/market-context"
);

const action = require(
  "../src/utils/action"
);

const {
  getNow,
} = require(
  "../src/services/now-service"
);

describe("Now service", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    repository
      .getLatestFinalizedPrice
      .mockResolvedValue({
        datetime_utc:
          "2026-07-21T00:00:00.000Z",
        actual_price: "23.09",
      });

    repository
      .getRecentFinalizedPrices
      .mockResolvedValue([
        { actual_price: "10.00" },
        { actual_price: "20.00" },
        { actual_price: "30.00" },
        { actual_price: "40.00" },
      ]);

    price
      .dollarsPerMwhToCentsPerKwh
      .mockReturnValue(2.31);

    freshness
      .getObservedPriceFreshness
      .mockReturnValue({
        confidence: "high",
        stale: false,
      });

    marketContext
      .getCurrentMarketDecision
      .mockReturnValue({
        contextKey:
          "about_average",
        level: "acceptable",
        explanationKey:
          "about_average",
      });

    action
      .getActionKey
      .mockReturnValue(
        "use_if_needed",
      );
  });

  test(
    "builds Now from the observed price instead of a forecast",
    async () => {
      await expect(
        getNow(),
      ).resolves.toEqual({
        generatedAt:
          "2026-07-21T00:00:00.000Z",
        confidence: "high",
        stale: false,

        price: {
          value: 2.31,
          unit: "¢/kWh",
          observedAtUtc:
            "2026-07-21T00:00:00.000Z",
        },

        recommendation: {
          level: "acceptable",
          explanationKey:
            "about_average",
          actionKey:
            "use_if_needed",
        },

        contextKey:
          "about_average",
      });

      expect(
        repository.getLatestFinalizedPrice,
      ).toHaveBeenCalledTimes(1);

      expect(
        repository.getRecentFinalizedPrices,
      ).toHaveBeenCalledTimes(1);

      expect(
        marketContext
          .getCurrentMarketDecision,
      ).toHaveBeenCalledWith(
        "23.09",
        expect.any(Array),
      );

      expect(
        freshness.getObservedPriceFreshness,
      ).toHaveBeenCalledWith(
        "2026-07-21T00:00:00.000Z",
      );
    },
  );

  test(
    "returns null when no observed price exists",
    async () => {
      repository
        .getLatestFinalizedPrice
        .mockResolvedValue(null);

      await expect(
        getNow(),
      ).resolves.toBeNull();
    },
  );
});
