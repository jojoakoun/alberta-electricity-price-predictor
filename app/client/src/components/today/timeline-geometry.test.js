import {
  describe,
  expect,
  test,
} from "vitest";

import {
  buildChartPoints,
  buildDayGroups,
  buildGridLines,
  buildPriceDomain,
  buildSmoothPath,
  buildTrendGradientStops,
  getPriceLabelY,
  PLOT_LEFT,
  PLOT_RIGHT,
} from "./timeline-geometry";

const forecasts = [
  {
    horizonHours: 1,
    priceCents: 2,
    targetTimeUtc: "2026-07-20T16:00:00.000Z",
  },
  {
    horizonHours: 3,
    priceCents: 2.1,
    targetTimeUtc: "2026-07-20T18:00:00.000Z",
  },
  {
    horizonHours: 6,
    priceCents: 4,
    targetTimeUtc: "2026-07-21T00:00:00.000Z",
  },
];

describe("timeline geometry", () => {
  test("spaces authentic forecast horizons evenly without inventing points", () => {
    const domain = buildPriceDomain(forecasts);
    const points = buildChartPoints(
      forecasts,
      domain.domainMinimum,
      domain.domainMaximum,
    );

    expect(points).toHaveLength(forecasts.length);
    expect(points[0].x).toBe(PLOT_LEFT);
    expect(points[points.length - 1].x).toBe(PLOT_RIGHT);
    expect(points[1].x - points[0].x).toBeCloseTo(
      points[2].x - points[1].x,
    );
  });

  test("builds a smooth guide through only the supplied points", () => {
    const points = [
      { x: 0, y: 10 },
      { x: 10, y: 20 },
      { x: 20, y: 5 },
    ];

    expect(buildSmoothPath([])).toBe("");
    expect(buildSmoothPath([points[0]])).toBe("M 0 10");
    expect(buildSmoothPath(points)).toBe(
      "M 0 10 C 5 10 5 20 10 20 C 15 20 15 5 20 5",
    );
  });

  test("moves a close alternating price label to prevent a collision", () => {
    const points = [
      { y: 100 },
      { y: 110 },
      { y: 120 },
    ];

    expect(getPriceLabelY(points, 0)).toBe(81);
    expect(getPriceLabelY(points, 1)).toBe(72);
    expect(getPriceLabelY(points, 2)).toBe(101);
  });

  test("groups consecutive points by their supplied day label", () => {
    const points = forecasts.map((forecast, index) => ({
      forecast,
      x: index * 10,
    }));
    const labels = new Map([
      [forecasts[0].targetTimeUtc, "Today"],
      [forecasts[1].targetTimeUtc, "Today"],
      [forecasts[2].targetTimeUtc, "Tomorrow"],
    ]);

    expect(
      buildDayGroups(
        points,
        (targetTimeUtc) => labels.get(targetTimeUtc),
      ),
    ).toEqual([
      { label: "Today", startX: 0, endX: 10 },
      { label: "Tomorrow", startX: 20, endX: 20 },
    ]);
  });

  test("returns aligned grid lines and a neutral or highlighted gradient", () => {
    const gridLines = buildGridLines(1, 4);
    const points = [
      { x: PLOT_LEFT },
      { x: (PLOT_LEFT + PLOT_RIGHT) / 2 },
      { x: PLOT_RIGHT },
    ];

    expect(gridLines.map(({ value }) => value)).toEqual([4, 3, 2, 1]);
    expect(gridLines[0].y).toBeLessThan(
      gridLines[gridLines.length - 1].y,
    );
    expect(buildTrendGradientStops(points, -1)).toEqual([
      { offset: "0%", color: "var(--color-okay)" },
      { offset: "100%", color: "var(--color-okay)" },
    ]);
    expect(buildTrendGradientStops(points, 1)).toEqual([
      { offset: "0%", color: "var(--color-okay)" },
      { offset: "0%", color: "var(--color-okay)" },
      { offset: "50%", color: "var(--color-brand)" },
      { offset: "100%", color: "var(--color-okay)" },
      { offset: "100%", color: "var(--color-okay)" },
    ]);
  });
});
