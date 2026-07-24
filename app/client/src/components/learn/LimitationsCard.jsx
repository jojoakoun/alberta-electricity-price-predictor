import {
  ChevronDown,
  CircleAlert,
} from "lucide-react";

import { copy } from "../../copy";

export function LimitationsCard() {
  const visibleLimits = [
    copy.learnPage.limits.items.prediction,
    copy.learnPage.limits.items.bill,
    copy.learnPage.limits.items.planning,
  ];

  return (
    <section
      aria-labelledby="important-limits"
      className="learn-limits"
    >
      <div className="learn-limits-card">
        <div className="space-y-[var(--space-2)]">
          <p className="product-eyebrow">
            {copy.learnPage.limits.eyebrow}
          </p>

          <h2 id="important-limits">
            {copy.learnPage.limits.title}
          </h2>

          <p className="text-[var(--color-text-muted)]">
            {copy.learnPage.limits.introduction}
          </p>
        </div>

        <ul className="learn-limit-highlights">
          {visibleLimits.map((item) => (
            <li key={item}>
              <CircleAlert
                aria-hidden="true"
                size={18}
              />

              <span>{item}</span>
            </li>
          ))}
        </ul>

        <details className="learn-limits-details">
          <summary>
            <span>
              {copy.learnPage.limits.detailsLabel}
            </span>

            <ChevronDown
              aria-hidden="true"
              size={20}
            />
          </summary>

          <div className="learn-limit-detail">
            <CircleAlert
              aria-hidden="true"
              size={18}
            />

            <span>
              {copy.learnPage.limits.items.events}
            </span>
          </div>
        </details>
      </div>
    </section>
  );
}
