const {
  classifyFutureForecastStatus,
  compareForecastWithObservedPrice,
  getFutureForecasts,
  selectBestTime,
} = require("../src/domain/today-selection");

function buildForecast({
  forecastKind = "model_forecast",
  horizonHours = 1,
  priceCents = 2,
  targetTimeUtc = "2026-07-18T21:00:00.000Z",
} = {}) {
  return {
    forecastKind,
    horizonHours,
    priceCents,
    targetTimeUtc,
  };
}

describe("Today selection", () => {
  test("excludes passed targets and the exact viewed-at boundary", () => {
    const forecasts = [
      buildForecast({
        horizonHours: 1,
        targetTimeUtc: "2026-07-18T19:00:00.000Z",
      }),
      buildForecast({
        horizonHours: 3,
        targetTimeUtc: "2026-07-18T20:00:00.000Z",
      }),
      buildForecast({
        horizonHours: 6,
        targetTimeUtc: "2026-07-18T21:00:00.000Z",
      }),
    ];

    expect(
      getFutureForecasts(
        forecasts,
        "2026-07-18T20:00:00.000Z",
      ),
    ).toEqual([forecasts[2]]);
  });

  test("rejects an invalid viewed-at timestamp with the exact error", () => {
    expect(
      () => getFutureForecasts([], "not-a-timestamp"),
    ).toThrow(
      new TypeError(
        "Best-time selection requires a valid viewedAt timestamp.",
      ),
    );
  });

  test("selects the first lowest model forecast and excludes other provenance", () => {
    const firstLowest = buildForecast({
      horizonHours: 3,
      priceCents: 1.5,
    });
    const forecasts = [
      buildForecast({
        forecastKind: "persistence_reference",
        horizonHours: 24,
        priceCents: 0.5,
      }),
      firstLowest,
      buildForecast({
        horizonHours: 6,
        priceCents: 1.5,
      }),
      buildForecast({
        forecastKind: "unknown",
        horizonHours: 12,
        priceCents: 0.25,
      }),
    ];

    expect(selectBestTime(forecasts)).toBe(firstLowest);
  });

  test("returns null when no eligible model forecast exists", () => {
    expect(
      selectBestTime([
        buildForecast({
          forecastKind: "persistence_reference",
        }),
        buildForecast({
          forecastKind: "unknown",
        }),
      ]),
    ).toBeNull();
  });

  test.each([
    [[], null, "none_remaining"],
    [[buildForecast()], buildForecast(), "available"],
    [
      [buildForecast({
        forecastKind: "persistence_reference",
      })],
      null,
      "reference_only",
    ],
    [
      [buildForecast({
        forecastKind: "unknown",
      })],
      null,
      "provenance_unavailable",
    ],
  ])(
    "classifies the future forecast state as %s / %s / %s",
    (futureForecasts, bestForecast, expectedStatus) => {
      expect(
        classifyFutureForecastStatus(
          futureForecasts,
          bestForecast,
        ),
      ).toBe(expectedStatus);
    },
  );

  test.each([
    [
      null,
      3,
      {
        comparison: "unavailable",
        priceDifferenceCents: null,
      },
    ],
    [
      buildForecast(),
      null,
      {
        comparison: "unavailable",
        priceDifferenceCents: null,
      },
    ],
  ])(
    "requires both forecast and observed-price evidence",
    (bestForecast, currentPriceCents, expected) => {
      expect(
        compareForecastWithObservedPrice(
          bestForecast,
          currentPriceCents,
        ),
      ).toEqual(expected);
    },
  );

  test.each([
    [3.141, 4, "forecast_lower", 0.86],
    [4, 3.141, "current_lower", 0.86],
    [3.14, 3.14, "forecast_equal", 0],
  ])(
    "compares already-public prices as %s versus %s",
    (
      forecastPriceCents,
      currentPriceCents,
      comparison,
      priceDifferenceCents,
    ) => {
      expect(
        compareForecastWithObservedPrice(
          buildForecast({
            priceCents: forecastPriceCents,
          }),
          currentPriceCents,
        ),
      ).toEqual({
        comparison,
        priceDifferenceCents,
      });
    },
  );
});
