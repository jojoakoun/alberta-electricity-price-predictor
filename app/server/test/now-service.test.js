jest.mock(
  "../src/repositories/hourly-price-repository"
);

jest.mock("../src/utils/price");
jest.mock("../src/utils/freshness");
jest.mock("../src/utils/market-context");
jest.mock("../src/utils/action");

const repository = require(
  "../src/repositories/hourly-price-repository"
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
  const viewedAt = new Date(
    "2026-07-24T04:13:00.000Z",
  );

  beforeEach(() => {
    jest.clearAllMocks();

    repository
      .getCurrentMarketPrice
      .mockResolvedValue({
        datetime_utc:
          "2026-07-24T04:00:00.000Z",
        price: "38.71",
        price_kind: "forecast",
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
      .mockReturnValue(3.87);

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
    "builds Now from the current-hour AESO value",
    async () => {
      await expect(
        getNow(viewedAt),
      ).resolves.toEqual({
        generatedAt:
          "2026-07-24T04:00:00.000Z",
        confidence: "high",
        stale: false,

        price: {
          value: 3.87,
          unit: "¢/kWh",
          kind: "forecast",
          sourceAtUtc:
            "2026-07-24T04:00:00.000Z",
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
        repository.getCurrentMarketPrice,
      ).toHaveBeenCalledWith(
        viewedAt,
      );

      expect(
        marketContext
          .getCurrentMarketDecision,
      ).toHaveBeenCalledWith(
        "38.71",
        expect.any(Array),
      );

      expect(
        freshness.getObservedPriceFreshness,
      ).toHaveBeenCalledWith(
        "2026-07-24T04:00:00.000Z",
        viewedAt,
      );
    },
  );

  test(
    "preserves an explicit finalized fallback kind",
    async () => {
      repository
        .getCurrentMarketPrice
        .mockResolvedValue({
          datetime_utc:
            "2026-07-24T02:00:00.000Z",
          price: "47.18",
          price_kind:
            "fallback_actual",
        });

      const result = await getNow(
        viewedAt,
      );

      expect(
        result.price.kind,
      ).toBe(
        "fallback_actual",
      );
    },
  );

  test(
    "returns null when no market price exists",
    async () => {
      repository
        .getCurrentMarketPrice
        .mockResolvedValue(null);

      await expect(
        getNow(viewedAt),
      ).resolves.toBeNull();
    },
  );
});
