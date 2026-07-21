import { TriangleAlert } from "lucide-react";

import { copy } from "../copy";

export function DelayedBanner({
  confidence,
  subject,
}) {
  const message = copy.freshness[subject][confidence];

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
          {message.title}
        </p>

        <p className="text-[var(--color-text-muted)]">
          {message.description}
        </p>
      </div>
    </div>
  );
}
