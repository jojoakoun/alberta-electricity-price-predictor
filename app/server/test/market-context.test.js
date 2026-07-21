const {
  getCurrentMarketDecision,
  getMarketContext,
} = require(
  "../src/utils/market-context"
);

describe("Market context", () => {
  const recentPrices = [
    { actual_price: "10.00" },
    { actual_price: "20.00" },
    { actual_price: "30.00" },
    { actual_price: "40.00" },
    { actual_price: "50.00" },
  ];

  test(
    "identifies a lower-than-usual current price",
    () => {
      expect(
        getMarketContext(
          "15.00",
          recentPrices,
        ),
      ).toBe(
        "lower_than_usual",
      );
    },
  );

  test(
    "identifies an about-average current price",
    () => {
      expect(
        getMarketContext(
          "30.00",
          recentPrices,
        ),
      ).toBe(
        "about_average",
      );
    },
  );

  test(
    "identifies a higher-than-usual current price",
    () => {
      expect(
        getMarketContext(
          "45.00",
          recentPrices,
        ),
      ).toBe(
        "higher_than_usual",
      );
    },
  );

  test(
    "recommends a low observed price",
    () => {
      expect(
        getCurrentMarketDecision(
          "15.00",
          recentPrices,
        ),
      ).toEqual({
        contextKey:
          "lower_than_usual",
        level: "recommended",
        explanationKey:
          "lower_than_usual",
      });
    },
  );

  test(
    "keeps a moderately high observed price acceptable",
    () => {
      expect(
        getCurrentMarketDecision(
          "45.00",
          recentPrices,
        ),
      ).toEqual({
        contextKey:
          "higher_than_usual",
        level: "acceptable",
        explanationKey:
          "about_average",
      });
    },
  );

  test(
    "avoids an extreme observed price",
    () => {
      expect(
        getCurrentMarketDecision(
          "75.00",
          recentPrices,
        ),
      ).toEqual({
        contextKey:
          "higher_than_usual",
        level: "avoid",
        explanationKey:
          "higher_than_usual",
      });
    },
  );

  test(
    "rejects an empty reference window",
    () => {
      expect(
        () => getCurrentMarketDecision(
          "30.00",
          [],
        ),
      ).toThrow(
        "Recent finalized prices are required.",
      );
    },
  );

  test(
    "rejects a malformed finalized price instead of silently ignoring it",
    () => {
      expect(
        () => getCurrentMarketDecision(
          "30.00",
          [
            { actual_price: "20.00" },
            { actual_price: "not-a-price" },
          ],
        ),
      ).toThrow(
        "Recent finalized price at index 1 must be a finite number.",
      );
    },
  );
});
