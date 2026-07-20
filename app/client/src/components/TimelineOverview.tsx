import type {
  CSSProperties,
} from "react";

import { copy } from "../copy";
import {
  formatAlbertaDay,
  formatAlbertaTime,
  formatNumber,
} from "../i18n/formatters";
import type {
  TodayBestTime,
  TodayForecast,
} from "../types/api";

type TimelineOverviewProps = {
  forecasts: TodayForecast[];
  bestTime: TodayBestTime;
  currentPriceCents?: number;
  referenceTimeUtc: string;
};

const WIDTH = 760;
const HEIGHT = 340;

const PLOT_LEFT = 112;
const PLOT_RIGHT = WIDTH - 38;
const PLOT_TOP = 56;
const PLOT_BOTTOM = HEIGHT - 92;

type ChartPoint = {
  forecast: TodayForecast;
  x: number;
  y: number;
};

type DayGroup = {
  label: string;
  startX: number;
  endX: number;
};

function scaleY(
  value: number,
  domainMinimum: number,
  domainMaximum: number,
) {
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
  forecasts: TodayForecast[],
  domainMinimum: number,
  domainMaximum: number,
): ChartPoint[] {
  const chartWidth =
    PLOT_RIGHT - PLOT_LEFT;

  return forecasts.map(
    (forecast, index) => ({
      forecast,

      // Equal spacing keeps all five genuine
      // forecast points readable.
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

function buildSmoothPath(
  points: ChartPoint[],
) {
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
  points: ChartPoint[],
  index: number,
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
  points: ChartPoint[],
  referenceTimeUtc: string,
): DayGroup[] {
  return points.reduce<DayGroup[]>(
    (groups, point) => {
      const label = formatAlbertaDay(
        point.forecast.targetTimeUtc,
        referenceTimeUtc,
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

export function TimelineOverview({
  forecasts,
  bestTime,
  currentPriceCents,
  referenceTimeUtc,
}: TimelineOverviewProps) {
  const forecastPrices = forecasts.map(
    (forecast) => forecast.priceCents,
  );

  const domainPrices =
    currentPriceCents === undefined
      ? forecastPrices
      : [
          ...forecastPrices,
          currentPriceCents,
        ];

  const rawMinimum = Math.min(
    ...domainPrices,
  );

  const rawMaximum = Math.max(
    ...domainPrices,
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

  const currentPriceY =
    currentPriceCents === undefined
      ? null
      : scaleY(
          currentPriceCents,
          domainMinimum,
          domainMaximum,
        );

  const dayGroups = buildDayGroups(
    points,
    referenceTimeUtc,
  );

  return (
    <section
      aria-labelledby="price-trend-title"
      className="today-chart-card"
    >
      <div className="space-y-[var(--space-1)]">
        <h2 id="price-trend-title">
          {copy.forecast.priceTrendTitle}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.forecast.priceTrendDescription}
        </p>
      </div>

      <svg
        aria-labelledby="price-trend-title"
        className="block h-auto w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      >
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

        {currentPriceY !== null
          && currentPriceCents !== undefined && (
          <g>
            <line
              stroke="var(--color-brand)"
              strokeDasharray="7 6"
              strokeWidth="2"
              x1={PLOT_LEFT}
              x2={PLOT_RIGHT}
              y1={currentPriceY}
              y2={currentPriceY}
            />

            <text
              className={[
                "fill-[var(--color-brand)]",
                "text-[12px] font-semibold",
              ].join(" ")}
              textAnchor="start"
              x={PLOT_LEFT + 10}
              y={Math.max(
                currentPriceY - 10,
                20,
              )}
            >
              {copy.forecast.currentPriceReference}
              {": "}
              {formatNumber(
                currentPriceCents,
              )}
              ¢
            </text>
          </g>
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
          className="today-chart-path"
          d={path}
          fill="none"
          stroke="var(--color-okay)"
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
              === bestTime.horizonHours;

            return (
              <g
                key={forecast.horizonHours}
                className="today-chart-point-group"
                style={{
                  "--point-delay":
                    `${240 + index * 80}ms`,
                } as CSSProperties}
              >
                {isBest && (
                  <circle
                    className="today-chart-best-halo"
                    cx={x}
                    cy={y}
                    r={17}
                  />
                )}

                <circle
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
                    "fill-[var(--color-text-muted)]",
                    "text-[12px]",
                  ].join(" ")}
                  textAnchor="middle"
                  x={x}
                  y={HEIGHT - 43}
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
            y={HEIGHT - 17}
          >
            {group.label}
          </text>
        ))}
      </svg>

      <ol className="sr-only">
        {forecasts.map((forecast) => (
          <li key={forecast.horizonHours}>
            {formatAlbertaDay(
              forecast.targetTimeUtc,
              referenceTimeUtc,
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
          </li>
        ))}
      </ol>
    </section>
  );
}
