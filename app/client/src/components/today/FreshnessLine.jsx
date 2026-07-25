import {
  Clock3,
  Info,
} from "lucide-react";

import { copy } from "../../copy";

import {
  formatAlbertaTime,
} from "../../i18n/formatters";


export function FreshnessLine({
  confidence,
  sourceDataAtUtc,
}) {
  const localTime = formatAlbertaTime(
    sourceDataAtUtc,
  );

  return (
    <div className="grid gap-[var(--space-2)]">
      {confidence === "moderate" && (
        <p
          className={[
            "flex items-start gap-[var(--space-2)]",
            "rounded-[var(--radius)]",
            "bg-[var(--color-okay-surface)]",
            "px-[var(--space-3)] py-[var(--space-2)]",
            "text-sm text-[var(--color-text-muted)]",
          ].join(" ")}
          data-testid="moderate-forecast-notice"
        >
          <Info
            aria-hidden="true"
            className="mt-0.5 shrink-0 text-[var(--color-okay)]"
            size={16}
          />

          <span>
            {
              copy.freshness.forecasts
                .moderate.description
            }
          </span>
        </p>
      )}

      <p
        className={[
          "flex items-center gap-[var(--space-2)]",
          "text-[var(--font-size-caption)]",
          "text-[var(--color-text-muted)]",
        ].join(" ")}
      >
        <Clock3
          aria-hidden="true"
          size={15}
        />

        <span>
          {
            copy.freshness
              .forecastsCalculatedThrough
          }{" "}
          {localTime}
        </span>
      </p>
    </div>
  );
}
