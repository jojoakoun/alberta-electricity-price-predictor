import {
  ChevronDown,
  Star,
  TriangleAlert,
} from "lucide-react";

import { copy } from "../copy";
import {
  formatAlbertaTime,
  formatNumber,
} from "../i18n/formatters";
import { isLowerPriceOpportunity } from "../domain/today";
import { StatusBadge } from "./StatusBadge";

export function ForecastList({
  forecasts,
  bestTime,
  comparison,
}) {
  const bestHorizon =
    isLowerPriceOpportunity(comparison)
      ? bestTime?.horizonHours
      : undefined;

  return (
    <section
      id="forecasts"
      aria-labelledby="forecasts-title"
      className={[
        "scroll-mt-[var(--space-5)]",
        "overflow-hidden rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "shadow-[var(--shadow-card)]",
      ].join(" ")}
    >
      <div
        className={[
          "border-b border-[var(--color-border)]",
          "px-[var(--space-4)] py-[var(--space-3)]",
        ].join(" ")}
      >
        <h2 id="forecasts-title">
          {copy.forecast.forecastDetails}
        </h2>
      </div>

      <div className="divide-y divide-[var(--color-border)]">
        {forecasts.map((forecast) => {
          const isBestTime =
            forecast.horizonHours
            === bestHorizon;

          const isPersistenceReference =
            forecast.forecastKind
            === "persistence_reference";

          return (
            <details
              key={forecast.horizonHours}
              className="group"
            >
              <summary
                className={[
                  "grid min-h-16 cursor-pointer list-none",
                  "grid-cols-[auto_1fr_auto_auto]",
                  "items-center gap-[var(--space-3)]",
                  "px-[var(--space-4)] py-[var(--space-3)]",
                  "hover:bg-[var(--color-brand-surface)]",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex h-8 w-8 items-center justify-center",
                    "rounded-full",
                    isBestTime
                      ? "bg-[var(--color-brand-surface)] text-[var(--color-brand)]"
                      : "text-[var(--color-okay)]",
                  ].join(" ")}
                >
                  {isBestTime ? (
                    <Star
                      aria-label={copy.forecast.bestTimeTitle}
                      data-testid="best-forecast-star"
                      size={20}
                      fill="currentColor"
                    />
                  ) : (
                    <span aria-hidden="true">—</span>
                  )}
                </span>

                <span className="min-w-0">
                  <span className="block font-semibold">
                    {formatAlbertaTime(forecast.targetTimeUtc)}
                  </span>

                  <span
                    className={[
                      "block truncate",
                      "text-[var(--font-size-caption)]",
                      "text-[var(--color-text-muted)]",
                    ].join(" ")}
                  >
                    {copy.temporal[forecast.temporalWordingKey]}
                  </span>

                  {isPersistenceReference && (
                    <span
                      className={[
                        "block",
                        "text-[var(--font-size-caption)]",
                        "font-semibold text-[var(--color-okay)]",
                      ].join(" ")}
                    >
                      {copy.forecast.persistenceReferenceTitle}
                    </span>
                  )}
                </span>

                <span
                  className={[
                    "whitespace-nowrap font-semibold",
                    isBestTime
                      ? "text-[var(--color-brand)]"
                      : "text-[var(--color-text)]",
                  ].join(" ")}
                >
                  {formatNumber(forecast.priceCents)} ¢/kWh
                </span>

                <ChevronDown
                  aria-hidden="true"
                  className={[
                    "transition-transform",
                    "duration-[var(--motion-duration)]",
                    "group-open:rotate-180",
                  ].join(" ")}
                  size={18}
                />
              </summary>

              <div
                className={[
                  "space-y-[var(--space-3)]",
                  "bg-[var(--color-bg)]",
                  "px-[var(--space-4)]",
                  "pb-[var(--space-4)] pt-[var(--space-3)]",
                ].join(" ")}
              >
                <StatusBadge
                  level={forecast.recommendation}
                />

                <p className="text-[var(--color-text-muted)]">
                  {copy.explanations[forecast.explanationKey]}
                </p>

                {isPersistenceReference ? (
                  <div
                    className={[
                      "flex items-start gap-[var(--space-2)]",
                      "rounded-[var(--radius)]",
                      "bg-[var(--color-okay-surface)]",
                      "p-[var(--space-3)]",
                    ].join(" ")}
                  >
                    <TriangleAlert
                      aria-hidden="true"
                      className={[
                        "mt-0.5 shrink-0",
                        "text-[var(--color-okay)]",
                      ].join(" ")}
                      size={18}
                    />

                    <div className="space-y-[var(--space-1)]">
                      <strong>
                        {copy.forecast.persistenceReferenceTitle}
                      </strong>

                      <p className="text-[var(--font-size-caption)]">
                        {copy.forecast.persistenceReferenceDescription}
                      </p>
                    </div>
                  </div>
                ) : forecast.horizonHours === 24 && (
                  <div
                    className={[
                      "flex items-start gap-[var(--space-2)]",
                      "rounded-[var(--radius)]",
                      "bg-[var(--color-okay-surface)]",
                      "p-[var(--space-3)]",
                    ].join(" ")}
                  >
                    <TriangleAlert
                      aria-hidden="true"
                      className={[
                        "mt-0.5 shrink-0",
                        "text-[var(--color-okay)]",
                      ].join(" ")}
                      size={18}
                    />

                    <p className="text-[var(--font-size-caption)]">
                      {copy.forecast.tomorrowCaution}
                    </p>
                  </div>
                )}
              </div>
            </details>
          );
        })}
      </div>
    </section>
  );
}
