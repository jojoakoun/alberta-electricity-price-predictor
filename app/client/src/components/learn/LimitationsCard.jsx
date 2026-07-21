import {
  ChevronDown,
  CircleAlert,
} from "lucide-react";

import { copy } from "../../copy";

export function LimitationsCard() {
  const limitItems = [
    copy.learnPage.limits.items.prediction,
    copy.learnPage.limits.items.events,
    copy.learnPage.limits.items.bill,
    copy.learnPage.limits.items.planning,
  ];
  return (
    <section
      aria-labelledby="important-limits"
      className="learn-limits"
    >
      <details className="learn-limits-details">
        <summary>
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

          <ChevronDown
            aria-hidden="true"
            size={22}
          />
        </summary>

        <ul className="learn-limit-list">
          {limitItems.map((item) => (
            <li key={item}>
              <CircleAlert
                aria-hidden="true"
                size={18}
              />

              <span>{item}</span>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
