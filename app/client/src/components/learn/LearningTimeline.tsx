import type {
  CSSProperties,
} from "react";
import {
  BarChart3,
  BrainCircuit,
  Database,
  Lightbulb,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

export function LearningTimeline() {
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
  return (
    <section
      aria-labelledby="how-wattwise-works"
      className="product-section-panel learn-process-panel"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="how-wattwise-works">
          {copy.learnPage.process.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.process.description}
        </p>

        <p
          className={[
            "text-[var(--font-size-caption)]",
            "text-[var(--color-text-muted)]",
          ].join(" ")}
        >
          {copy.learnPage.process.modelReview}
        </p>
      </div>

      <ol className="learn-timeline">
        {processSteps.map(
          ({
            number,
            Icon,
            title,
            description,
          }, index) => (
            <li
              key={title}
              className="learn-timeline-step"
              style={{
                "--learn-step-delay": `${120 + index * 90}ms`,
              } as CSSProperties}
            >
              <span className="learn-timeline-node">
                <Icon
                  aria-hidden="true"
                  size={19}
                  strokeWidth={2}
                />
              </span>

              <Card className="learn-timeline-card product-interactive-card">
                <p className="product-eyebrow">
                  {copy.learnPage.process.stepLabel}{" "}
                  {number}
                </p>

                <h3>{title}</h3>

                <p className="text-[var(--color-text-muted)]">
                  {description}
                </p>
              </Card>
            </li>
          ),
        )}
      </ol>
    </section>
  );
}
