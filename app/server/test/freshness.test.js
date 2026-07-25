const {
  getObservedPriceFreshness,
  getPredictionFreshness,
} = require("../src/utils/freshness");

describe("Freshness calculation", () => {
  const now = new Date("2026-07-18T20:00:00.000Z");
  const minuteMs = 60 * 1000;

  function atAge(ageMs) {
    return new Date(
      now.getTime() - ageMs,
    ).toISOString();
  }

  describe("prediction source data", () => {
    test.each([
      [75 * minuteMs - 1, "high", false],
      [75 * minuteMs, "high", false],
      [75 * minuteMs + 1, "moderate", true],
      [150 * minuteMs - 1, "moderate", true],
      [150 * minuteMs, "moderate", true],
      [150 * minuteMs + 1, "low", true],
    ])(
      "classifies an age of %i milliseconds",
      (ageMs, confidence, stale) => {
        expect(
          getPredictionFreshness(
            atAge(ageMs),
            now,
          ),
        ).toEqual({ confidence, stale });
      },
    );

    test("treats routine 120-minute source-data age as delayed", () => {
      expect(
        getPredictionFreshness(
          atAge(120 * minuteMs),
          now,
        ),
      ).toEqual({
        confidence: "moderate",
        stale: true,
      });
    });
  });

  describe("finalized observed prices", () => {
    test.each([
      [150 * minuteMs - 1, "high", false],
      [150 * minuteMs, "high", false],
      [150 * minuteMs + 1, "moderate", true],
      [240 * minuteMs - 1, "moderate", true],
      [240 * minuteMs, "moderate", true],
      [240 * minuteMs + 1, "low", true],
    ])(
      "classifies an age of %i milliseconds",
      (ageMs, confidence, stale) => {
        expect(
          getObservedPriceFreshness(
            atAge(ageMs),
            now,
          ),
        ).toEqual({ confidence, stale });
      },
    );

    test.each([60, 75, 90, 120, 135, 150])(
      "treats a routine AESO latency of %i minutes as current",
      (ageMinutes) => {
        expect(
          getObservedPriceFreshness(
            atAge(ageMinutes * minuteMs),
            now,
          ),
        ).toEqual({
          confidence: "high",
          stale: false,
        });
      },
    );

    test("marks a genuinely old observed price as stale", () => {
      expect(
        getObservedPriceFreshness(
          atAge(6 * 60 * minuteMs),
          now,
        ),
      ).toEqual({
        confidence: "low",
        stale: true,
      });
    });
  });

  test.each([
    [getPredictionFreshness, "generatedAt"],
    [getObservedPriceFreshness, "observedAtUtc"],
  ])(
    "rejects invalid and future %s timestamps",
    (getFreshness, timestampName) => {
      expect(() =>
        getFreshness("not-a-date", now),
      ).toThrow("Freshness requires valid dates.");

      expect(() =>
        getFreshness(
          "2026-07-18T20:00:00.001Z",
          now,
        ),
      ).toThrow(
        `${timestampName} cannot be in the future.`,
      );
    },
  );
});
