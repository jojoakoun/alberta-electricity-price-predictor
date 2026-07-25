const {
  normalizeRecommendation,
} = require("../src/utils/recommendation");

describe("Recommendation normalization", () => {
  test.each([
    ["Recommended", "recommended"],
    ["Acceptable", "acceptable"],
    ["Avoid", "avoid"],
  ])("maps %s to %s", (storedValue, publicValue) => {
    expect(normalizeRecommendation(storedValue)).toBe(publicValue);
  });

  test("rejects an unknown recommendation", () => {
    expect(() => normalizeRecommendation("Unknown")).toThrow(
      "Unsupported recommendation: Unknown",
    );
  });
});
