import {
  useId,
} from "react";

import { copy } from "../copy";
import { isLowerPriceOpportunity } from "../domain/today";
import {
  formatAlbertaDay,
  formatAlbertaTime,
  formatNumber,
} from "../i18n/formatters";

const WIDTH = 760;
const HEIGHT = 380;

const PLOT_LEFT = 112;
const PLOT_RIGHT = WIDTH - 38;
const PLOT_TOP = 56;
const PLOT_BOTTOM = 255;

function scaleY(value, domainMinimum, domainMaximum) {
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

function buildChartPoints(
  forecasts,
  domainMinimum,
  domainMaximum,
) {
  const chartWidth =
    PLOT_RIGHT - PLOT_LEFT;

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
      y: scaleY(
        forecast.priceCents,
        domainMinimum,
        domainMaximum,
      ),
    }),
  );
}

function buildSmoothPath(points) {
  if (points.length === 0) {
    return "";
  }

  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y}`;
  }

  let path =
    `M ${points[0].x} ${points[0].y}`;

  for (
    let index = 0;
    index < points.length - 1;
    index += 1
  ) {
    const current = points[index];
    const next = points[index + 1];

    const midpointX =
      (current.x + next.x) / 2;

    path += [
      ` C ${midpointX} ${current.y}`,
      `${midpointX} ${next.y}`,
      `${next.x} ${next.y}`,
    ].join(" ");
  }

  return path;
}

function getPriceLabelY(
  points,
  index,
) {
  const point = points[index];
  const previous = points[index - 1];

  const closeToPrevious =
    previous !== undefined
    && Math.abs(point.y - previous.y) < 34;

  const offset =
    closeToPrevious && index % 2 === 1
      ? -38
      : -19;

  return Math.max(
    point.y + offset,
    24,
  );
}

function buildDayGroups(
  points,
  forecastSourceTimeUtc,
) {
  return points.reduce(
    (groups, point) => {
      const label = formatAlbertaDay(
        point.forecast.targetTimeUtc,
        forecastSourceTimeUtc,
      );

      const currentGroup =
        groups[groups.length - 1];

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

function getHorizontalOffset(x) {
  const percentage =
    (
      (x - PLOT_LEFT)
      / (PLOT_RIGHT - PLOT_LEFT)
    )
    * 100;

  return `${Math.min(
    100,
    Math.max(
      0,
      percentage,
    ),
  )}%`;
}

function buildTrendGradientStops(
  points,
  bestPointIndex,
) {
  const regularColor =
    "var(--color-okay)";

  const bestColor =
    "var(--color-brand)";

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

  const bestPoint =
    points[bestPointIndex];

  if (bestPointIndex === 0) {
    const nextPoint =
      points[Math.min(
        1,
        points.length - 1,
      )];

    return [
      {
        offset: "0%",
        color: bestColor,
      },
      {
        offset: getHorizontalOffset(
          nextPoint.x,
        ),
        color: regularColor,
      },
      {
        offset: "100%",
        color: regularColor,
      },
    ];
  }

  const previousPoint =
    points[bestPointIndex - 1];

  if (
    bestPointIndex
    === points.length - 1
  ) {
    return [
      {
        offset: "0%",
        color: regularColor,
      },
      {
        offset: getHorizontalOffset(
          previousPoint.x,
        ),
        color: regularColor,
      },
      {
        offset: getHorizontalOffset(
          bestPoint.x,
        ),
        color: bestColor,
      },
    ];
  }

  const nextPoint =
    points[bestPointIndex + 1];

  return [
    {
      offset: "0%",
      color: regularColor,
    },
    {
      offset: getHorizontalOffset(
        previousPoint.x,
      ),
      color: regularColor,
    },
    {
      offset: getHorizontalOffset(
        bestPoint.x,
      ),
      color: bestColor,
    },
    {
      offset: getHorizontalOffset(
        nextPoint.x,
      ),
      color: regularColor,
    },
    {
      offset: "100%",
      color: regularColor,
    },
  ];
}

export function TimelineOverview({
  forecasts,
  bestTime,
  comparison,
  currentPriceCents,
  currentObservedAtUtc,
  forecastSourceTimeUtc,
}) {
  const gradientId = useId()
    .replace(
      /:/g,
      "",
    );

  if (forecasts.length === 0) {
    return null;
  }

  const forecastPrices = forecasts.map(
    (forecast) => forecast.priceCents,
  );

  const rawMinimum = Math.min(
    ...forecastPrices,
  );

  const rawMaximum = Math.max(
    ...forecastPrices,
  );

  const rawRange = Math.max(
    rawMaximum - rawMinimum,
    0.5,
  );

  const verticalMargin = Math.max(
    rawRange * 0.16,
    0.4,
  );

  const domainMinimum = Math.max(
    0,
    rawMinimum - verticalMargin,
  );

  const domainMaximum =
    rawMaximum + verticalMargin;

  const points = buildChartPoints(
    forecasts,
    domainMinimum,
    domainMaximum,
  );

  const path = buildSmoothPath(points);

  const bestHorizon =
    isLowerPriceOpportunity(comparison)
      ? bestTime?.horizonHours
      : undefined;

  const bestPointIndex = bestHorizon === undefined
    ? -1
    : points.findIndex(
        ({ forecast }) =>
          forecast.horizonHours
          === bestHorizon,
      );

  const trendGradientStops =
    buildTrendGradientStops(
      points,
      bestPointIndex,
    );

  const gridValues = Array.from(
    { length: 4 },
    (_, index) =>
      domainMaximum
      - (
        index
        * (
          domainMaximum
          - domainMinimum
        )
      ) / 3,
  );

  const dayGroups = buildDayGroups(
    points,
    forecastSourceTimeUtc,
  );

  const persistenceReference =
    forecasts.find(
      (forecast) =>
        forecast.forecastKind
        === "persistence_reference",
    );

  return (
    <section
      aria-labelledby="price-trend-title"
      aria-describedby="price-trend-description"
      className="today-chart-card"
    >
      <div className="space-y-[var(--space-1)]">
        <h2 id="price-trend-title">
          {copy.forecast.priceTrendTitle}
        </h2>

        <p
          id="price-trend-description"
          className="text-[var(--color-text-muted)]"
        >
          {copy.forecast.priceTrendDescription}
        </p>
      </div>

      {currentPriceCents != null && (
        <div
          className={[
            "mt-[var(--space-4)]",
            "flex flex-wrap items-center justify-between",
            "gap-[var(--space-3)]",
            "rounded-[var(--radius-lg)]",
            "border border-[var(--color-border)]",
            "bg-[var(--color-surface-muted)]",
            "px-[var(--space-4)] py-[var(--space-3)]",
          ].join(" ")}
        >
          <div>
            <p className="font-semibold text-[var(--color-text)]">
              {copy.forecast.currentObservedPriceLabel}
            </p>

            <p className="text-sm text-[var(--color-text-muted)]">
              {currentObservedAtUtc
                ? [
                    copy.freshness.observed,
                    formatAlbertaTime(
                      currentObservedAtUtc,
                    ),
                  ].join(" ")
                : copy.forecast.currentPriceReference}
            </p>
          </div>

          <p className="text-xl font-semibold text-[var(--color-brand)]">
            {formatNumber(currentPriceCents)}
            <span className="ml-1 text-sm">
              ¢/kWh
            </span>
          </p>
        </div>
      )}

      <svg
        aria-labelledby="price-trend-title"
        aria-describedby="price-trend-description"
        className="block h-auto w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      >
        <defs>
          <linearGradient
            id={gradientId}
            data-testid="forecast-trend-gradient"
            gradientUnits="userSpaceOnUse"
            x1={PLOT_LEFT}
            x2={PLOT_RIGHT}
            y1="0"
            y2="0"
          >
            {trendGradientStops.map(
              (stop, index) => (
                <stop
                  key={`${stop.offset}-${index}`}
                  offset={stop.offset}
                  stopColor={stop.color}
                />
              ),
            )}
          </linearGradient>
        </defs>

        {gridValues.map(
          (value, index) => {
            const y =
              PLOT_TOP
              + (
                index
                * (
                  PLOT_BOTTOM
                  - PLOT_TOP
                )
              ) / 3;

            return (
              <g key={index}>
                <line
                  className="stroke-[var(--color-border)]"
                  strokeDasharray="4 7"
                  strokeWidth="1"
                  x1={PLOT_LEFT}
                  x2={PLOT_RIGHT}
                  y1={y}
                  y2={y}
                />

                <text
                  className={[
                    "fill-[var(--color-text-muted)]",
                    "text-[12px]",
                  ].join(" ")}
                  textAnchor="end"
                  x={PLOT_LEFT - 26}
                  y={y + 4}
                >
                  {formatNumber(value, 1)}¢
                </text>
              </g>
            );
          },
        )}

        <path
          className="today-chart-path-base"
          d={path}
          fill="none"
          stroke="var(--color-border)"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="6"
        />

        <path
          data-testid="forecast-trend-path"
          className="today-chart-path"
          d={path}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />

        {points.map(
          (
            {
              forecast,
              x,
              y,
            },
            index,
          ) => {
            const isBest =
              forecast.horizonHours
              === bestHorizon;

            return (
              <g
                key={forecast.horizonHours}
                className="today-chart-point-group"
                style={{
                  "--point-delay":
                    `${240 + index * 80}ms`,
                }}
              >
                {isBest && (
                  <circle
                    data-testid="best-forecast-halo"
                    className="today-chart-best-halo"
                    cx={x}
                    cy={y}
                    r={17}
                  />
                )}

                <circle
                  data-testid={`forecast-point-${forecast.horizonHours}`}
                  cx={x}
                  cy={y}
                  fill={
                    isBest
                      ? "var(--color-brand)"
                      : "var(--color-okay)"
                  }
                  r={isBest ? 9 : 7}
                />

                <text
                  className={[
                    "fill-[var(--color-text)]",
                    "text-[13px] font-semibold",
                  ].join(" ")}
                  textAnchor="middle"
                  x={x}
                  y={getPriceLabelY(
                    points,
                    index,
                  )}
                >
                  {formatNumber(
                    forecast.priceCents,
                  )}
                  ¢
                </text>

                <text
                  className={[
                    "fill-[var(--color-brand)]",
                    "text-[11px] font-semibold",
                  ].join(" ")}
                  textAnchor="middle"
                  x={x}
                  y={308}
                >
                  +{forecast.horizonHours} h
                </text>

                <text
                  className={[
                    "fill-[var(--color-text-muted)]",
                    "text-[12px]",
                  ].join(" ")}
                  textAnchor="middle"
                  x={x}
                  y={332}
                >
                  {formatAlbertaTime(
                    forecast.targetTimeUtc,
                  )}
                </text>
              </g>
            );
          },
        )}

        {dayGroups.map((group) => (
          <text
            key={group.label}
            className={[
              "fill-[var(--color-brand)]",
              "text-[11px] font-semibold",
            ].join(" ")}
            textAnchor="middle"
            x={
              (
                group.startX
                + group.endX
              ) / 2
            }
            y={362}
          >
            {group.label}
          </text>
        ))}
      </svg>

      {persistenceReference && (
        <div
          className={[
            "flex flex-wrap items-start justify-between",
            "gap-[var(--space-2)]",
            "rounded-[var(--radius)]",
            "border border-[var(--color-okay)]",
            "bg-[var(--color-okay-surface)]",
            "px-[var(--space-4)] py-[var(--space-3)]",
          ].join(" ")}
        >
          <div className="max-w-2xl space-y-[var(--space-1)]">
            <strong className="text-[var(--color-okay)]">
              {copy.forecast.persistenceReferenceTitle}
            </strong>

            <p className="text-sm text-[var(--color-text-muted)]">
              {copy.forecast.persistenceReferenceDescription}
            </p>
          </div>

          <span className="text-sm text-[var(--color-text-muted)]">
            +{persistenceReference.horizonHours} h
            {" · "}
            {formatAlbertaDay(
              persistenceReference.targetTimeUtc,
              forecastSourceTimeUtc,
            )}
            {" · "}
            {formatAlbertaTime(
              persistenceReference.targetTimeUtc,
            )}
          </span>
        </div>
      )}

      <ol className="sr-only">
        {forecasts.map((forecast) => (
          <li key={forecast.horizonHours}>
            +{forecast.horizonHours} h
            {", "}
            {formatAlbertaDay(
              forecast.targetTimeUtc,
              forecastSourceTimeUtc,
            )}
            {", "}
            {formatAlbertaTime(
              forecast.targetTimeUtc,
            )}
            {": "}
            {formatNumber(
              forecast.priceCents,
            )}
            {" ¢/kWh"}
            {forecast.forecastKind
              === "persistence_reference"
              ? `, ${copy.forecast.persistenceReferenceTitle}`
              : ""}
          </li>
        ))}
      </ol>
    </section>
  );
}
