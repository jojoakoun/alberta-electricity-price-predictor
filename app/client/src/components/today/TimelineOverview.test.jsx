import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  test,
} from "vitest";

import {
  setLanguage,
} from "../../i18n/language";

import {
  TimelineOverview,
} from "./TimelineOverview";


const forecasts = [
  {
    horizonHours: 1,
    targetTimeUtc:
      "2026-07-20T16:00:00.000Z",
    targetTimeLocal:
      "2026-07-20T10:00:00",
    temporalWordingKey:
      "very_soon",
    priceCents: 2.05,
    recommendation:
      "acceptable",
    explanationKey:
      "acceptable_market_risk",
    forecastKind:
      "model_forecast",
  },
  {
    horizonHours: 3,
    targetTimeUtc:
      "2026-07-20T18:00:00.000Z",
    targetTimeLocal:
      "2026-07-20T12:00:00",
    temporalWordingKey:
      "in_a_few_hours",
    priceCents: 2.32,
    recommendation:
      "acceptable",
    explanationKey:
      "acceptable_market_risk",
    forecastKind:
      "model_forecast",
  },
  {
    horizonHours: 6,
    targetTimeUtc:
      "2026-07-20T21:00:00.000Z",
    targetTimeLocal:
      "2026-07-20T15:00:00",
    temporalWordingKey:
      "this_afternoon",
    priceCents: 4.54,
    recommendation: "avoid",
    explanationKey:
      "higher_than_usual",
    forecastKind:
      "model_forecast",
  },
  {
    horizonHours: 12,
    targetTimeUtc:
      "2026-07-21T03:00:00.000Z",
    targetTimeLocal:
      "2026-07-20T21:00:00",
    temporalWordingKey:
      "this_evening",
    priceCents: 5.2,
    recommendation: "avoid",
    explanationKey:
      "higher_than_usual",
    forecastKind:
      "model_forecast",
  },
  {
    horizonHours: 24,
    targetTimeUtc:
      "2026-07-21T15:00:00.000Z",
    targetTimeLocal:
      "2026-07-21T09:00:00",
    temporalWordingKey:
      "tomorrow_around_this_time",
    priceCents: 1.3,
    recommendation:
      "recommended",
    explanationKey:
      "lower_than_usual",
    forecastKind:
      "persistence_reference",
  },
];

const bestTime = {
  horizonHours: 1,
  targetTimeUtc:
    "2026-07-20T16:00:00.000Z",
  targetTimeLocal:
    "2026-07-20T10:00:00",
  priceCents: 2.05,
  recommendation:
    "acceptable",
};


function readPointX(testId) {
  return Number(
    screen
      .getByTestId(testId)
      .getAttribute("cx"),
  );
}


describe("TimelineOverview", () => {
  beforeEach(() => {
    setLanguage("en");
  });

  afterEach(() => {
    cleanup();
  });

  test(
    "draws the current price followed by five authentic horizons",
    () => {
      render(
        <TimelineOverview
          forecasts={forecasts}
          bestTime={bestTime}
          comparison="forecast_lower"
          currentPriceCents={2.5}
          currentPriceSourceAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
          forecastSourceTimeUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      expect(
        screen.getByTestId(
          "current-price-point",
        ),
      ).toHaveAttribute(
        "fill",
        "var(--color-text)",
      );

      for (
        const horizon of [
          1,
          3,
          6,
          12,
          24,
        ]
      ) {
        expect(
          screen.getByTestId(
            `forecast-point-${horizon}`,
          ),
        ).toBeInTheDocument();
      }

      expect(
        screen.getAllByText(
          "Now",
        ).length,
      ).toBeGreaterThan(0);

      expect(
        screen.getByText(
          /The first point is the current AESO market price/i,
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByTestId(
          "best-forecast-halo",
        ),
      ).toBeInTheDocument();
    },
  );

  test(
    "includes the current price in the chart scale and line",
    () => {
      render(
        <TimelineOverview
          forecasts={forecasts}
          bestTime={bestTime}
          comparison="unavailable"
          currentPriceCents={8}
          currentPriceSourceAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
          forecastSourceTimeUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      const currentY = Number(
        screen
          .getByTestId(
            "current-price-point",
          )
          .getAttribute("cy"),
      );

      const forecastY = Number(
        screen
          .getByTestId(
            "forecast-point-24",
          )
          .getAttribute("cy"),
      );

      expect(
        currentY,
      ).toBeLessThan(
        forecastY,
      );

      expect(
        screen
          .getByTestId(
            "forecast-trend-path",
          )
          .getAttribute("d"),
      ).toContain(" C ");
    },
  );

  test(
    "spaces all six supplied points evenly",
    () => {
      render(
        <TimelineOverview
          forecasts={forecasts}
          bestTime={bestTime}
          comparison="unavailable"
          currentPriceCents={2.5}
          currentPriceSourceAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
          forecastSourceTimeUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      const pointIds = [
        "current-price-point",
        "forecast-point-1",
        "forecast-point-3",
        "forecast-point-6",
        "forecast-point-12",
        "forecast-point-24",
      ];

      const positions =
        pointIds.map(
          readPointX,
        );

      const spacings =
        positions
          .slice(1)
          .map(
            (position, index) =>
              position
              - positions[index],
          );

      spacings.forEach(
        (spacing) => {
          expect(
            spacing,
          ).toBeCloseTo(
            spacings[0],
            5,
          );
        },
      );
    },
  );

  test(
    "never promotes the current point as bestTime",
    () => {
      render(
        <TimelineOverview
          forecasts={forecasts}
          bestTime={bestTime}
          comparison="forecast_lower"
          currentPriceCents={0.1}
          currentPriceSourceAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
          forecastSourceTimeUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      expect(
        screen.getByTestId(
          "current-price-point",
        ),
      ).toHaveAttribute(
        "fill",
        "var(--color-text)",
      );

      expect(
        screen.getByTestId(
          "forecast-point-1",
        ),
      ).toHaveAttribute(
        "fill",
        "var(--color-brand)",
      );
    },
  );

  test(
    "keeps the persistence reference visible",
    () => {
      render(
        <TimelineOverview
          forecasts={forecasts}
          bestTime={bestTime}
          comparison="unavailable"
          currentPriceCents={2.5}
          currentPriceSourceAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
          forecastSourceTimeUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      expect(
        screen.getByText(
          "Persistence reference",
        ),
      ).toBeInTheDocument();
    },
  );
});
