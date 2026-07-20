import { Check } from "lucide-react";

import { copy } from "../copy";
import type { NowResponse } from "../types/api";
import { Card } from "./Card";
import { FreshnessLine } from "./FreshnessLine";
import { StatusBadge } from "./StatusBadge";

type RecommendationCardProps = {
  data: NowResponse;
};

export function RecommendationCard({
  data,
}: RecommendationCardProps) {
  const { recommendation } = data;

  return (
    <Card className="space-y-[var(--space-5)]">
      <StatusBadge level={recommendation.level} />

      <div className="space-y-[var(--space-3)]">
        <p className="text-[var(--color-text)]">
          {copy.recommendations[recommendation.level].defaultExplanation}
        </p>

        <div
          className={[
            "flex items-center gap-[var(--space-2)]",
            "font-semibold text-[var(--color-brand)]",
          ].join(" ")}
        >
          <Check
            aria-hidden="true"
            className="shrink-0"
            size={18}
            strokeWidth={2.5}
          />

          <p>{copy.actions[recommendation.actionKey]}</p>
        </div>
      </div>

      <div
        className={[
          "space-y-[var(--space-2)]",
          "border-t border-[var(--color-border)]",
          "pt-[var(--space-5)]",
        ].join(" ")}
      >
        <p
          className={[
            "text-[var(--font-size-caption)]",
            "text-[var(--color-text-muted)]",
          ].join(" ")}
        >
          {copy.price.label}
        </p>

        <p className="text-[2.5rem] font-bold leading-none">
          {data.price.value.toFixed(2)} {data.price.unit}
        </p>

        <p className="text-[var(--color-text-muted)]">
          {copy.context[data.contextKey]}
        </p>
      </div>

      <div
        className={[
          "border-t border-[var(--color-border)]",
          "pt-[var(--space-3)]",
        ].join(" ")}
      >
        <FreshnessLine generatedAt={data.generatedAt} />
      </div>
    </Card>
  );
}
