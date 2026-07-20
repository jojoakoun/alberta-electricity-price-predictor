import type {
  TodayBestTime,
  TodayForecast,
} from "../types/api";

type TimelineOverviewProps = {
  forecasts: TodayForecast[];
  bestTime: TodayBestTime;
};

const WIDTH = 720;
const HEIGHT = 300;
const PADDING_LEFT = 62;
const PADDING_RIGHT = 32;
const PADDING_TOP = 48;
const PADDING_BOTTOM = 64;

type ChartPoint = {
  forecast: TodayForecast;
  x: number;
  y: number;
};

function buildChartPoints(
  forecasts: TodayForecast[],
): ChartPoint[] {
  const prices = forecasts.map(
    (forecast) => forecast.priceCents,
  );

  const minimum = Math.min(...prices);
  const maximum = Math.max(...prices);
  const range = Math.max(maximum - minimum, 0.1);

  const chartWidth =
    WIDTH - PADDING_LEFT - PADDING_RIGHT;

  const chartHeight =
    HEIGHT - PADDING_TOP - PADDING_BOTTOM;

  return forecasts.map((forecast, index) => ({
    forecast,

    x:
      PADDING_LEFT +
      (index * chartWidth) /
        Math.max(forecasts.length - 1, 1),

    y:
      PADDING_TOP +
      ((maximum - forecast.priceCents) / range) *
        chartHeight,
  }));
}

function buildSmoothPath(points: ChartPoint[]) {
  if (points.length === 0) {
    return "";
  }

  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y}`;
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let index = 0; index < points.length - 1; index += 1) {
    const current = points[index];
    const next = points[index + 1];

    const midpointX = (current.x + next.x) / 2;

    path += [
      `C ${midpointX} ${current.y}`,
      `${midpointX} ${next.y}`,
      `${next.x} ${next.y}`,
    ].join(" ");
  }

  return path;
}

export function TimelineOverview({
  forecasts,
  bestTime,
}: TimelineOverviewProps) {
  const points = buildChartPoints(forecasts);
  const path = buildSmoothPath(points);

  const prices = forecasts.map(
    (forecast) => forecast.priceCents,
  );

  const minimum = Math.min(...prices);
  const maximum = Math.max(...prices);

  const gridValues = [
    maximum,
    maximum - (maximum - minimum) / 3,
    maximum - ((maximum - minimum) * 2) / 3,
    minimum,
  ];

  return (
    <section
      aria-labelledby="price-trend-title"
      className={[
        "space-y-[var(--space-3)]",
        "rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "p-[var(--space-3)]",
        "shadow-[var(--shadow-card)]",
        "sm:p-[var(--space-4)]",
      ].join(" ")}
    >
      <h2 id="price-trend-title">
        Price trend
      </h2>

      <svg
        aria-labelledby="price-trend-title"
        className="block h-auto w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      >
        <defs>
          <linearGradient
            id="forecast-line-gradient"
            x1="0%"
            x2="100%"
            y1="0%"
            y2="0%"
          >
            <stop
              offset="0%"
              stopColor="var(--color-okay)"
            />

            <stop
              offset="42%"
              stopColor="var(--color-okay)"
            />

            <stop
              offset="58%"
              stopColor="var(--color-brand)"
            />

            <stop
              offset="75%"
              stopColor="var(--color-okay)"
            />

            <stop
              offset="100%"
              stopColor="var(--color-okay)"
            />
          </linearGradient>
        </defs>

        {gridValues.map((value, index) => {
          const y =
            PADDING_TOP +
            (index *
              (HEIGHT -
                PADDING_TOP -
                PADDING_BOTTOM)) /
              Math.max(gridValues.length - 1, 1);

          return (
            <g key={value}>
              <line
                className="stroke-[var(--color-border)]"
                strokeDasharray="4 7"
                strokeWidth="1"
                x1={PADDING_LEFT}
                x2={WIDTH - PADDING_RIGHT}
                y1={y}
                y2={y}
              />

              <text
                className={[
                  "fill-[var(--color-text-muted)]",
                  "text-[12px]",
                ].join(" ")}
                textAnchor="end"
                x={PADDING_LEFT - 12}
                y={y + 4}
              >
                {value.toFixed(1)}¢
              </text>
            </g>
          );
        })}

        <path
          d={path}
          fill="none"
          stroke="url(#forecast-line-gradient)"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />

        {points.map(({ forecast, x, y }) => {
          const isBest =
            forecast.horizonHours ===
            bestTime.horizonHours;

          return (
            <g key={forecast.horizonHours}>
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
                y={Math.max(y - 18, 20)}
              >
                {forecast.priceCents.toFixed(2)}¢
              </text>

              <text
                className={[
                  "fill-[var(--color-text-muted)]",
                  "text-[12px]",
                ].join(" ")}
                textAnchor="middle"
                x={x}
                y={HEIGHT - 22}
              >
                {forecast.targetTimeLocal}
              </text>
            </g>
          );
        })}
      </svg>

      <ol className="sr-only">
        {forecasts.map((forecast) => (
          <li key={forecast.horizonHours}>
            {forecast.targetTimeLocal}:{" "}
            {forecast.priceCents.toFixed(2)} cents per
            kilowatt-hour
          </li>
        ))}
      </ol>
    </section>
  );
}
