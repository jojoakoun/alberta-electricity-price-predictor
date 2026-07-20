import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import {
  afterEach,
  describe,
  expect,
  test,
} from "vitest";

import type {
  TodayBestTime,
  TodayForecast,
} from "../types/api";
import { TimelineOverview } from "./TimelineOverview";

afterEach(() => {
  cleanup();
});

const forecasts: TodayForecast[] = [
  {
    horizonHours: 1,
    targetTimeUtc: "2026-07-20T16:00:00.000Z",
    targetTimeLocal: "2026-07-20T10:00:00",
    temporalWordingKey: "very_soon",
    priceCents: 2.05,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
  },
  {
    horizonHours: 3,
    targetTimeUtc: "2026-07-20T18:00:00.000Z",
    targetTimeLocal: "2026-07-20T12:00:00",
    temporalWordingKey: "in_a_few_hours",
    priceCents: 2.32,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
  },
  {
    horizonHours: 6,
    targetTimeUtc: "2026-07-20T21:00:00.000Z",
    targetTimeLocal: "2026-07-20T15:00:00",
    temporalWordingKey: "this_afternoon",
    priceCents: 4.54,
    recommendation: "avoid",
    explanationKey: "higher_than_usual",
  },
  {
    horizonHours: 12,
    targetTimeUtc: "2026-07-21T03:00:00.000Z",
    targetTimeLocal: "2026-07-20T21:00:00",
    temporalWordingKey: "this_evening",
    priceCents: 5.2,
    recommendation: "avoid",
    explanationKey: "higher_than_usual",
  },
  {
    horizonHours: 24,
    targetTimeUtc: "2026-07-21T15:00:00.000Z",
    targetTimeLocal: "2026-07-21T09:00:00",
    temporalWordingKey:
      "tomorrow_around_this_time",
    priceCents: 1.3,
    recommendation: "recommended",
    explanationKey: "lower_than_usual",
  },
];

const bestTime: TodayBestTime = {
  horizonHours: 24,
  targetTimeUtc: "2026-07-21T15:00:00.000Z",
  targetTimeLocal: "2026-07-21T09:00:00",
  priceCents: 1.3,
  recommendation: "recommended",
};

function readPointX(
  horizonHours: number,
) {
  const point = screen.getByTestId(
    `forecast-point-${horizonHours}`,
  );

  return Number(
    point.getAttribute("cx"),
  );
}

describe("TimelineOverview", () => {
  test("separates the observed price from the forecasts", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        currentPriceCents={1.3}
        currentObservedAtUtc="2026-07-20T14:00:00.000Z"
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    expect(
      screen.getByText(
        /Price observed at 8:00 a.m./i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getAllByText("+1 h").length,
    ).toBeGreaterThan(0);

    expect(
      screen.getAllByText("+24 h").length,
    ).toBeGreaterThan(0);

    expect(
      screen.getByText(
        "Same as observed price",
      ),
    ).toBeInTheDocument();
  });

  test("uses a smooth line only as a visual guide", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    const path = screen.getByTestId(
      "forecast-trend-path",
    );

    expect(
      path.getAttribute("d"),
    ).toContain(" C ");

    expect(
      screen.getByText(
        /The smooth line is only a visual guide/i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Values between the dots are not model predictions/i,
      ),
    ).toBeInTheDocument();
  });

  test("spaces the five forecast points evenly for readability", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    const spacings = [
      readPointX(3) - readPointX(1),
      readPointX(6) - readPointX(3),
      readPointX(12) - readPointX(6),
      readPointX(24) - readPointX(12),
    ];

    spacings.forEach((spacing) => {
      expect(spacing).toBeCloseTo(
        spacings[0],
        5,
      );
    });
  });

  test("gradually changes the curve from orange to green at the lowest forecast", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        currentPriceCents={2.5}
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    const path = screen.getByTestId(
      "forecast-trend-path",
    );

    const gradient = screen.getByTestId(
      "forecast-trend-gradient",
    );

    const stops = Array.from(
      gradient.querySelectorAll("stop"),
    );

    expect(
      path.getAttribute("stroke"),
    ).toMatch(
      /^url\(#.+\)$/,
    );

    expect(
      stops.map(
        (stop) =>
          stop.getAttribute(
            "stop-color",
          ),
      ),
    ).toEqual([
      "var(--color-okay)",
      "var(--color-okay)",
      "var(--color-brand)",
    ]);
  });

  test("keeps the lowest forecast highlighted when it matches the observed price", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        currentPriceCents={1.3}
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    expect(
      screen.getByTestId(
        "best-forecast-halo",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByTestId(
        "forecast-point-24",
      ),
    ).toHaveAttribute(
      "fill",
      "var(--color-brand)",
    );

    expect(
      screen.getByTestId(
        "forecast-point-12",
      ),
    ).toHaveAttribute(
      "fill",
      "var(--color-okay)",
    );
  });

  test("shows the best-time highlight when the forecast is lower", () => {
    render(
      <TimelineOverview
        forecasts={forecasts}
        bestTime={bestTime}
        currentPriceCents={2.5}
        referenceTimeUtc="2026-07-20T15:00:00.000Z"
      />,
    );

    expect(
      screen.getByTestId(
        "best-forecast-halo",
      ),
    ).toBeInTheDocument();
  });
});
