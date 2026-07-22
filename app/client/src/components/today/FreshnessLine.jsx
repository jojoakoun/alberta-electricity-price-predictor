import { Clock3 } from "lucide-react";

import { copy } from "../../copy";
import { formatAlbertaTime } from "../../i18n/formatters";

export function FreshnessLine({
  sourceDataAtUtc,
}) {
  const localTime = formatAlbertaTime(sourceDataAtUtc);

  return (
    <p
      className={[
        "flex items-center gap-[var(--space-2)]",
        "text-[var(--font-size-caption)]",
        "text-[var(--color-text-muted)]",
      ].join(" ")}
    >
      <Clock3 aria-hidden="true" size={16} strokeWidth={2} />
      {copy.freshness.forecastsCalculatedThrough} {localTime}
    </p>
  );
}
