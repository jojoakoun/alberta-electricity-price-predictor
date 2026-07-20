import { TriangleAlert } from "lucide-react";

import { copy } from "../copy";

type DelayedBannerProps = {
  confidence: "moderate" | "low";
};

export function DelayedBanner({
  confidence,
}: DelayedBannerProps) {
  return (
    <div
      role="status"
      className={[
        "flex items-start gap-[var(--space-2)]",
        "rounded-[var(--radius)]",
        "border border-[var(--color-okay)]",
        "bg-[var(--color-okay-surface)]",
        "p-[var(--space-3)]",
        "text-[var(--color-text)]",
      ].join(" ")}
    >
      <TriangleAlert
        aria-hidden="true"
        className="mt-0.5 shrink-0 text-[var(--color-okay)]"
        size={20}
        strokeWidth={2}
      />

      <div>
        <p className="font-medium">
          {copy.freshness.delayed}
        </p>

        <p className="text-[var(--color-text-muted)]">
          {copy.confidence[confidence]}
        </p>
      </div>
    </div>
  );
}
