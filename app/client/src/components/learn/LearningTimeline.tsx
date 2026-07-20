import {
  BarChart3,
  BrainCircuit,
  Database,
  Lightbulb,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

const processSteps = [
  {
    number: "01",
    Icon: Database,
    ...copy.learnPage.process.steps.data,
  },
  {
    number: "02",
    Icon: BarChart3,
    ...copy.learnPage.process.steps.patterns,
  },
  {
    number: "03",
    Icon: BrainCircuit,
    ...copy.learnPage.process.steps.forecasts,
  },
  {
    number: "04",
    Icon: Lightbulb,
    ...copy.learnPage.process.steps.recommendation,
  },
] as const;

export function LearningTimeline() {
  return (
    <section
      aria-labelledby="how-wattwise-works"
      className="space-y-[var(--space-4)]"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="how-wattwise-works">
          {copy.learnPage.process.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.process.description}
        </p>
      </div>

      <ol className="space-y-[var(--space-3)]">
        {processSteps.map(
          (
            {
              number,
              Icon,
              title,
              description,
            },
            index,
          ) => {
            const hasNextStep =
              index < processSteps.length - 1;

            return (
              <li
                key={title}
                className={[
                  "relative grid",
                  "grid-cols-[2.5rem_minmax(0,1fr)]",
                  "gap-[var(--space-3)]",
                ].join(" ")}
              >
                {hasNextStep && (
                  <span
                    aria-hidden="true"
                    className={[
                      "absolute left-[1.21875rem]",
                      "top-10 -bottom-[var(--space-3)]",
                      "w-px",
                      "bg-[var(--color-border)]",
                    ].join(" ")}
                  />
                )}

                <span
                  className={[
                    "relative z-10",
                    "flex h-10 w-10",
                    "items-center justify-center",
                    "rounded-full",
                    "border border-[var(--color-brand)]",
                    "bg-[var(--color-surface)]",
                    "text-[var(--color-brand)]",
                  ].join(" ")}
                >
                  <Icon
                    aria-hidden="true"
                    size={18}
                    strokeWidth={2}
                  />
                </span>

                <Card
                  className={[
                    "space-y-[var(--space-2)]",
                    "p-[var(--space-3)]",
                    "sm:p-[var(--space-4)]",
                  ].join(" ")}
                >
                  <p
                    className={[
                      "font-semibold uppercase tracking-wide",
                      "text-[var(--font-size-caption)]",
                      "text-[var(--color-brand)]",
                    ].join(" ")}
                  >
                    Step {number}
                  </p>

                  <h3>{title}</h3>

                  <p
                    className={[
                      "max-w-2xl",
                      "text-[var(--color-text-muted)]",
                    ].join(" ")}
                  >
                    {description}
                  </p>
                </Card>
              </li>
            );
          },
        )}
      </ol>
    </section>
  );
}
