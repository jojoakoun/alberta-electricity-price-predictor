export const CHART_WIDTH = 760;
export const CHART_HEIGHT = 380;

export const PLOT_LEFT = 112;
export const PLOT_RIGHT = CHART_WIDTH - 38;
export const PLOT_TOP = 56;
export const PLOT_BOTTOM = 255;

export function buildPriceDomain(forecasts) {
  const forecastPrices = forecasts.map(
    (forecast) => forecast.priceCents,
  );
  const rawMinimum = Math.min(...forecastPrices);
  const rawMaximum = Math.max(...forecastPrices);
  const rawRange = Math.max(rawMaximum - rawMinimum, 0.5);
  const verticalMargin = Math.max(rawRange * 0.16, 0.4);

  return {
    domainMinimum: Math.max(0, rawMinimum - verticalMargin),
    domainMaximum: rawMaximum + verticalMargin,
  };
}

export function scalePriceY(value, domainMinimum, domainMaximum) {
  const range = Math.max(
    domainMaximum - domainMinimum,
    0.1,
  );

  return (
    PLOT_TOP
    + (
      (domainMaximum - value)
      / range
    )
      * (PLOT_BOTTOM - PLOT_TOP)
  );
}

export function buildChartPoints(
  forecasts,
  domainMinimum,
  domainMaximum,
) {
  const chartWidth = PLOT_RIGHT - PLOT_LEFT;

  // Even visual spacing keeps the five authentic horizons readable without
  // inventing intermediate hourly forecast points.
  return forecasts.map(
    (forecast, index) => ({
      forecast,
      x:
        PLOT_LEFT
        + (
          index
          * chartWidth
        )
          / Math.max(
            forecasts.length - 1,
            1,
          ),
      y: scalePriceY(
        forecast.priceCents,
        domainMinimum,
        domainMaximum,
      ),
    }),
  );
}

export function buildSmoothPath(points) {
  if (points.length === 0) {
    return "";
  }

  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y}`;
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (
    let index = 0;
    index < points.length - 1;
    index += 1
  ) {
    const current = points[index];
    const next = points[index + 1];
    const midpointX = (current.x + next.x) / 2;

    path += [
      ` C ${midpointX} ${current.y}`,
      `${midpointX} ${next.y}`,
      `${next.x} ${next.y}`,
    ].join(" ");
  }

  return path;
}

export function getPriceLabelY(points, index) {
  const point = points[index];
  const previous = points[index - 1];
  const closeToPrevious = (
    previous !== undefined
    && Math.abs(point.y - previous.y) < 34
  );
  const offset = (
    closeToPrevious && index % 2 === 1
      ? -38
      : -19
  );

  return Math.max(point.y + offset, 24);
}

export function buildDayGroups(points, getDayLabel) {
  return points.reduce(
    (groups, point) => {
      const label = getDayLabel(point.forecast.targetTimeUtc);
      const currentGroup = groups[groups.length - 1];

      if (
        currentGroup
        && currentGroup.label === label
      ) {
        currentGroup.endX = point.x;

        return groups;
      }

      groups.push({
        label,
        startX: point.x,
        endX: point.x,
      });

      return groups;
    },
    [],
  );
}

export function buildGridLines(domainMinimum, domainMaximum) {
  return Array.from(
    { length: 4 },
    (_, index) => ({
      value:
        domainMaximum
        - (
          index
          * (
            domainMaximum
            - domainMinimum
          )
        ) / 3,
      y:
        PLOT_TOP
        + (
          index
          * (
            PLOT_BOTTOM
            - PLOT_TOP
          )
        ) / 3,
    }),
  );
}

function getHorizontalOffset(x) {
  const percentage = (
    (x - PLOT_LEFT)
    / (PLOT_RIGHT - PLOT_LEFT)
  ) * 100;

  return `${Math.min(
    100,
    Math.max(0, percentage),
  )}%`;
}

export function buildTrendGradientStops(points, bestPointIndex) {
  const regularColor = "var(--color-okay)";
  const bestColor = "var(--color-brand)";

  if (
    points.length === 0
    || bestPointIndex < 0
  ) {
    return [
      {
        offset: "0%",
        color: regularColor,
      },
      {
        offset: "100%",
        color: regularColor,
      },
    ];
  }

  const bestPoint = points[bestPointIndex];

  if (bestPointIndex === 0) {
    const nextPoint = points[Math.min(1, points.length - 1)];

    return [
      {
        offset: "0%",
        color: bestColor,
      },
      {
        offset: getHorizontalOffset(nextPoint.x),
        color: regularColor,
      },
      {
        offset: "100%",
        color: regularColor,
      },
    ];
  }

  const previousPoint = points[bestPointIndex - 1];

  if (bestPointIndex === points.length - 1) {
    return [
      {
        offset: "0%",
        color: regularColor,
      },
      {
        offset: getHorizontalOffset(previousPoint.x),
        color: regularColor,
      },
      {
        offset: getHorizontalOffset(bestPoint.x),
        color: bestColor,
      },
    ];
  }

  const nextPoint = points[bestPointIndex + 1];

  return [
    {
      offset: "0%",
      color: regularColor,
    },
    {
      offset: getHorizontalOffset(previousPoint.x),
      color: regularColor,
    },
    {
      offset: getHorizontalOffset(bestPoint.x),
      color: bestColor,
    },
    {
      offset: getHorizontalOffset(nextPoint.x),
      color: regularColor,
    },
    {
      offset: "100%",
      color: regularColor,
    },
  ];
}
