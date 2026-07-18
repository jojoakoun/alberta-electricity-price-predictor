import {
  CheckCircle2,
  Clock3,
  MinusCircle,
  TriangleAlert,
} from "lucide-react";

import { copy } from "../copy";
import type { RecommendationLevel } from "../types/recommendation";

type StatusBadgeProps = {
  level: RecommendationLevel;
};

const statusStyles: Record<
  RecommendationLevel,
  {
    background: string;
    foreground: string;
    Icon: typeof CheckCircle2;
  }
> = {
  recommended: {
    background: "bg-[var(--color-good-surface)]",
    foreground: "text-[var(--color-good)]",
    Icon: CheckCircle2,
  },

  acceptable: {
    background: "bg-[var(--color-okay-surface)]",
    foreground: "text-[var(--color-okay)]",
    Icon: MinusCircle,
  },

  avoid: {
    background: "bg-[var(--color-wait-surface)]",
    foreground: "text-[var(--color-wait)]",
    Icon: Clock3,
  },

  unavailable: {
    background: "bg-[var(--color-error-surface)]",
    foreground: "text-[var(--color-error)]",
    Icon: TriangleAlert,
  },
};

export function StatusBadge({ level }: StatusBadgeProps) {
  const {
    background,
    foreground,
    Icon,
  } = statusStyles[level];

  return (
    <span
      className={[
        "inline-flex min-h-11 items-center gap-[var(--space-2)]",
        "rounded-[var(--radius)]",
        "px-[var(--space-3)] py-[var(--space-2)]",
        "font-medium",
        background,
        foreground,
      ].join(" ")}
    >
      <Icon aria-hidden="true" size={20} strokeWidth={2} />
      {copy.recommendations[level].label}
    </span>
  );
}
