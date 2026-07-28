import { copy } from "../../copy";
import {
  formatElectricityPrice,
} from "../../utils/electricity-price";
import { isLowerPriceOpportunity } from "../../domain/today";
import {
  formatAlbertaDay,
  formatAlbertaTime,
  formatNumber,
} from "../../i18n/formatters";
import {
  getRecommendationColor,
} from "./recommendation-color";
import {
  buildChartPoints,
  buildDayGroups,
  buildGridLines,
  buildPriceDomain,
  buildSmoothPath,
  CHART_HEIGHT,
  CHART_WIDTH,
  getPriceLabelY,
  PLOT_LEFT,
  PLOT_RIGHT,
} from "./timeline-geometry";

export function TimelineOverview({
  forecasts,
  bestTime,
  comparison,
  currentPriceCents,
  currentPriceSourceAtUtc,
  forecastSourceTimeUtc,
}) {
  if (forecasts.length === 0) {
    return null;
  }

  const currentPoint = (
    currentPriceCents != null
    && currentPriceSourceAtUtc
  )
    ? {
        forecastKind:
          "current_market_price",
        horizonHours: 0,
        pointKind: "current",
        priceCents:
          currentPriceCents,
        targetTimeUtc:
          currentPriceSourceAtUtc,
      }
    : null;

  const chartEntries = [
    ...(currentPoint
      ? [currentPoint]
      : []),
    ...forecasts.map(
      (forecast) => ({
        ...forecast,
        pointKind: "forecast",
      }),
    ),
  ];

  const {
    domainMinimum,
    domainMaximum,
  } = buildPriceDomain(
    chartEntries,
  );

  const points = buildChartPoints(
    chartEntries,
    domainMinimum,
    domainMaximum,
  );

  const path = buildSmoothPath(points);

  const bestHorizon =
    isLowerPriceOpportunity(comparison)
      ? bestTime?.horizonHours
      : undefined;

  // When the current market price is already the lowest option,
  // treat the first chart point as the highlighted opportunity.
  const bestPointIndex = comparison === "current_lower"
    ? 0
    : bestHorizon === undefined
      ? -1
      : points.findIndex(
          ({ forecast }) =>
            forecast.horizonHours
            === bestHorizon,
        );

  const gridLines = buildGridLines(
    domainMinimum,
    domainMaximum,
  );

  const dayGroups = buildDayGroups(
    points,
    (targetTimeUtc) => formatAlbertaDay(
      targetTimeUtc,
      forecastSourceTimeUtc,
    ),
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

        <div
          aria-label="Price recommendation legend"
          className="today-chart-legend"
        >
          <span>
            <i
              aria-hidden="true"
              className="today-chart-legend-dot today-chart-legend-good"
            />
            {copy.recommendations.recommended.label}
          </span>

          <span>
            <i
              aria-hidden="true"
              className="today-chart-legend-dot today-chart-legend-okay"
            />
            {copy.recommendations.acceptable.label}
          </span>

          <span>
            <i
              aria-hidden="true"
              className="today-chart-legend-dot today-chart-legend-wait"
            />
            {copy.recommendations.avoid.label}
          </span>

          <span>
            <i
              aria-hidden="true"
              className="today-chart-legend-halo"
            />
            Best option
          </span>
        </div>

        <p
          id="price-trend-description"
          className="text-[var(--color-text-muted)]"
        >
          {copy.forecast.priceTrendDescription}
        </p>
      </div>

      <svg
        aria-labelledby="price-trend-title"
        aria-describedby="price-trend-description"
        className="block h-auto w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
      >

        {gridLines.map(
          ({ value, y }, index) => (
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
          ),
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
          stroke="var(--color-text-muted)"
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
            const isCurrent =
              forecast.pointKind
              === "current";

            // Use the already-calculated index so the halo works
            // for both the current point and future forecast points.
            const isBest = index === bestPointIndex;

            return (
              <g
                key={
                  isCurrent
                    ? "current"
                    : forecast.horizonHours
                }
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
                  data-testid={
                    isCurrent
                      ? "current-price-point"
                      : `forecast-point-${forecast.horizonHours}`
                  }
                  cx={x}
                  cy={y}
                  fill={
                    isCurrent
                      ? comparison === "current_lower"
                        ? "var(--color-brand)"
                        : "var(--color-text)"
                      : getRecommendationColor(
                          forecast.recommendation,
                        )
                  }
                  r={
                    isCurrent
                      ? 8
                      : isBest
                        ? 9
                        : 7
                  }
                />

                <text
                  className={[
                    "fill-[var(--color-text)]",
                    "text-[13px] font-semibold",
                  ].join(" ")}
                  textAnchor="middle"
                  x={x}
                  y={
                    getPriceLabelY(
                    points,
                    index,
                  )
                    - (isBest ? 14 : 0)
                  }
                >
                  {formatElectricityPrice(
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
                  {isCurrent
                    ? copy.forecast.nowLabel
                    : `+${forecast.horizonHours} h`}
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
        {chartEntries.map((forecast) => (
          <li
            key={
              forecast.pointKind === "current"
                ? "current"
                : forecast.horizonHours
            }
          >
            {forecast.pointKind === "current"
              ? copy.forecast.nowLabel
              : `+${forecast.horizonHours} h`}
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
            {formatElectricityPrice(
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
