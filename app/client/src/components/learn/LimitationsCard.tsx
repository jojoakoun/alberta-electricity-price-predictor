import {
  ChevronDown,
  CircleAlert,
} from "lucide-react";

import { copy } from "../../copy";

const limitItems = [
  copy.learnPage.limits.items.prediction,
  copy.learnPage.limits.items.events,
  copy.learnPage.limits.items.bill,
  copy.learnPage.limits.items.planning,
] as const;

export function LimitationsCard() {
  return (
    <section aria-labelledby="important-limits">
      <details
        className={[
          "group overflow-hidden",
          "rounded-[var(--radius)]",
          "border border-[var(--color-okay)]",
          "bg-[var(--color-okay-surface)]",
          "shadow-[var(--shadow-card)]",
        ].join(" ")}
      >
        <summary
          className={[
            "flex min-h-14 cursor-pointer",
            "list-none items-center",
            "justify-between",
            "gap-[var(--space-3)]",
            "px-[var(--space-4)]",
            "py-[var(--space-3)]",
          ].join(" ")}
        >
          <div className="space-y-[var(--space-1)]">
            <h2 id="important-limits">
              {copy.learnPage.limits.title}
            </h2>

            <p className="text-[var(--color-text-muted)]">
              {copy.learnPage.limits.introduction}
            </p>
          </div>

          <ChevronDown
            aria-hidden="true"
            className={[
              "shrink-0",
              "text-[var(--color-okay)]",
              "transition-transform",
              "group-open:rotate-180",
            ].join(" ")}
            size={22}
          />
        </summary>

        <ul
          className={[
            "space-y-[var(--space-3)]",
            "border-t border-[var(--color-okay)]",
            "px-[var(--space-4)]",
            "py-[var(--space-4)]",
          ].join(" ")}
        >
          {limitItems.map((item) => (
            <li
              key={item}
              className={[
                "flex items-start",
                "gap-[var(--space-2)]",
              ].join(" ")}
            >
              <CircleAlert
                aria-hidden="true"
                className={[
                  "mt-0.5 shrink-0",
                  "text-[var(--color-okay)]",
                ].join(" ")}
                size={18}
              />

              <span className="text-[var(--color-text-muted)]">
                {item}
              </span>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
