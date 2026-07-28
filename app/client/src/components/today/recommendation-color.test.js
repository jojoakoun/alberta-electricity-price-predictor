import {
  describe,
  expect,
  test,
} from "vitest";

import {
  getRecommendationColor,
} from "./recommendation-color";

describe("forecast recommendation colors", () => {
  test.each([
    [
      "recommended",
      "var(--color-brand)",
    ],
    [
      "acceptable",
      "var(--color-okay)",
    ],
    [
      "avoid",
      "var(--color-wait)",
    ],
  ])(
    "maps %s to its product color",
    (recommendation, expectedColor) => {
      expect(
        getRecommendationColor(recommendation),
      ).toBe(expectedColor);
    },
  );

  test("uses a neutral fallback for an unknown recommendation", () => {
    expect(
      getRecommendationColor("unknown"),
    ).toBe("var(--color-text)");
  });
});
