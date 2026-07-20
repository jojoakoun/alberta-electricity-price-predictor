import { Star } from "lucide-react";

import { copy } from "../copy";
import type { TodayBestTime } from "../types/api";
import { Card } from "./Card";
import { StatusBadge } from "./StatusBadge";

type BestTimeCardProps = {
  bestTime: TodayBestTime;
};

export function BestTimeCard({
  bestTime,
}: BestTimeCardProps) {
  return (
    <Card
      className={[
        "space-y-[var(--space-4)]",
        "border-[var(--color-brand)]",
        "p-[var(--space-5)]",
      ].join(" ")}
    >
      <div
        className={[
          "flex items-center gap-[var(--space-2)]",
          "font-semibold uppercase",
          "text-[var(--color-brand)]",
        ].join(" ")}
      >
        <Star
          aria-hidden="true"
          fill="currentColor"
          size={24}
          strokeWidth={2}
        />

        <h2>{copy.forecast.bestTimeTitle}</h2>
      </div>

      <div
        className={[
          "flex flex-col gap-[var(--space-4)]",
          "sm:flex-row sm:items-end sm:justify-between",
        ].join(" ")}
      >
        <div className="space-y-[var(--space-2)]">
          <p className="text-[2.75rem] font-bold leading-none">
            {bestTime.targetTimeLocal}
          </p>

          <p className="text-[2rem] font-semibold leading-none">
            {bestTime.priceCents.toFixed(2)} ¢/kWh
          </p>
        </div>

        <StatusBadge level={bestTime.recommendation} />
      </div>

      <p className="text-[var(--color-text-muted)]">
        {copy.forecast.bestTimeExplanation}
      </p>
    </Card>
  );
}
