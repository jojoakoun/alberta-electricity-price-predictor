import {
  CircleDollarSign,
  House,
} from "lucide-react";

import { copy } from "../copy";

export function AudienceNotice() {
  return (
    <section
      aria-labelledby="wattwise-audience-title"
      className="audience-notice-full"
    >
      <div className="audience-full-primary">
        <span className="audience-full-icon">
          <House
            aria-hidden="true"
            size={23}
            strokeWidth={2}
          />
        </span>

        <div className="space-y-[var(--space-2)]">
          <p className="product-eyebrow">
            {copy.audience.title}
          </p>

          <h2 id="wattwise-audience-title">
            {copy.audience.primary}
          </h2>

          <p className="text-[var(--color-text-muted)]">
            {copy.audience.detail}
          </p>
        </div>
      </div>

      <div className="audience-full-fixed">
        <span className="audience-fixed-icon">
          <CircleDollarSign
            aria-hidden="true"
            size={21}
          />
        </span>

        <div className="space-y-[var(--space-1)]">
          <h3>{copy.audience.fixedTitle}</h3>

          <p>{copy.audience.fixedDetail}</p>
        </div>
      </div>
    </section>
  );
}
