import { Clock3 } from "lucide-react";

import { copy } from "../copy";

type FreshnessLineProps = {
  generatedAt: string;
};

export function FreshnessLine({
  generatedAt,
}: FreshnessLineProps) {
  const date = new Date(generatedAt);

  const localTime = new Intl.DateTimeFormat("en-CA", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);

  return (
    <p
      className={[
        "flex items-center gap-[var(--space-2)]",
        "text-[var(--font-size-caption)]",
        "text-[var(--color-text-muted)]",
      ].join(" ")}
    >
      <Clock3 aria-hidden="true" size={16} strokeWidth={2} />
      {copy.freshness.updated} {localTime}
    </p>
  );
}
