const {
  getExplanationKey,
} = require("../src/utils/explanation");

describe("Explanation mapping", () => {
  test.each([
    [
      "Predicted price is favorable compared with the recent market.",
      "lower_than_usual",
    ],
    [
      "Predicted price is acceptable but market risk is increasing.",
      "acceptable_market_risk",
    ],
    [
      "Predicted price is high compared with the recent market.",
      "higher_than_usual",
    ],
  ])("maps a persisted explanation to %s", (storedValue, publicKey) => {
    expect(getExplanationKey(storedValue)).toBe(publicKey);
  });

  test("rejects an unknown persisted explanation", () => {
    expect(() => getExplanationKey("Unexpected explanation")).toThrow(
      "Unsupported persisted explanation.",
    );
  });
});
