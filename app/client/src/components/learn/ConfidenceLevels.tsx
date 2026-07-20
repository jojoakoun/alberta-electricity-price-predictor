import {
  Activity,
  CircleAlert,
  Clock3,
  Gauge,
  TriangleAlert,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

const confidenceHorizons = [
  {
    Icon: Gauge,
    score: 100,
    ...copy.learnPage.confidence.horizons.one,
  },
  {
    Icon: Clock3,
    score: 84,
    ...copy.learnPage.confidence.horizons.three,
  },
  {
    Icon: Activity,
    score: 70,
    ...copy.learnPage.confidence.horizons.six,
  },
  {
    Icon: TriangleAlert,
    score: 52,
    ...copy.learnPage.confidence.horizons.twelve,
  },
  {
    Icon: CircleAlert,
    score: 34,
    ...copy.learnPage.confidence.horizons.twentyFour,
  },
] as const;

export function ConfidenceLevels() {
  return (
    <section
      aria-labelledby="forecast-confidence"
      className="space-y-[var(--space-4)]"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="forecast-confidence">
          {copy.learnPage.confidence.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.confidence.description}
        </p>
      </div>

      <Card className="space-y-[var(--space-4)]">
        {confidenceHorizons.map(
          ({
            Icon,
            label,
            detail,
            score,
          }) => (
            <div
              key={label}
              className="space-y-[var(--space-2)]"
            >
              <div
                className={[
                  "flex flex-col gap-[var(--space-1)]",
                  "sm:flex-row sm:items-center",
                  "sm:justify-between",
                ].join(" ")}
              >
                <div
                  className={[
                    "flex items-center",
                    "gap-[var(--space-2)]",
                  ].join(" ")}
                >
                  <Icon
                    aria-hidden="true"
                    className="text-[var(--color-brand)]"
                    size={19}
                  />

                  <span className="font-semibold">
                    {label}
                  </span>
                </div>

                <span
                  className={[
                    "pl-7",
                    "text-[var(--font-size-caption)]",
                    "text-[var(--color-text-muted)]",
                    "sm:pl-0",
                  ].join(" ")}
                >
                  {detail}
                </span>
              </div>

              <div
                role="progressbar"
                aria-label={`${label} relative confidence`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={score}
                className={[
                  "h-2 overflow-hidden",
                  "rounded-full",
                  "bg-[var(--color-border)]",
                ].join(" ")}
              >
                <div
                  className={[
                    "h-full rounded-full",
                    "bg-[var(--color-brand)]",
                  ].join(" ")}
                  style={{
                    width: `${score}%`,
                  }}
                />
              </div>
            </div>
          ),
        )}
      </Card>
    </section>
  );
}
