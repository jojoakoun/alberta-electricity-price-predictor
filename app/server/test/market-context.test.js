const { getMarketContext } = require("../src/utils/market-context");

describe("Market context", () => {
  const recentPrices = [
    { actual_price: "10.00" },
    { actual_price: "20.00" },
    { actual_price: "30.00" },
    { actual_price: "40.00" },
    { actual_price: "50.00" },
  ];

  test("identifies a lower-than-usual current price", () => {
    expect(getMarketContext("15.00", recentPrices)).toBe(
      "lower_than_usual",
    );
  });

  test("identifies an about-average current price", () => {
    expect(getMarketContext("30.00", recentPrices)).toBe(
      "about_average",
    );
  });

  test("identifies a higher-than-usual current price", () => {
    expect(getMarketContext("45.00", recentPrices)).toBe(
      "higher_than_usual",
    );
  });

  test("rejects an empty reference window", () => {
    expect(() => getMarketContext("30.00", [])).toThrow(
      "Recent finalized prices are required.",
    );
  });
});
