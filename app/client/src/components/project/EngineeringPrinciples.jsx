import {
  CheckCircle2,
} from "lucide-react";

import { Reveal } from "../motion/Reveal";
import { Card } from "../Card";
import { copy } from "../../copy";

export function EngineeringPrinciples() {
  const principles = copy.projectPage.principles;

  return (
    <Reveal>
      <section
        aria-labelledby="engineering-principles"
        className="project-section-panel project-section-soft"
      >
        <div className="max-w-2xl space-y-[var(--space-2)]">
          <h2 id="engineering-principles">
            {principles.title}
          </h2>

          <p className="text-[var(--color-text-muted)]">
            {principles.description}
          </p>
        </div>

        <div className="grid gap-[var(--space-3)] md:grid-cols-2">
          {principles.items.map(
            ({
              title,
              description,
            }, index) => (
              <Card
                key={title}
                className={[
                  "project-stagger-item",
                  "project-interactive-card",
                  "flex items-start gap-[var(--space-3)]",
                ].join(" ")}
                style={{
                  "--item-delay": `${index * 55}ms`,
                }}
              >
                <CheckCircle2
                  aria-hidden="true"
                  className={[
                    "project-principle-icon",
                    "mt-0.5 shrink-0",
                    "text-[var(--color-brand)]",
                  ].join(" ")}
                  size={21}
                />

                <div className="space-y-[var(--space-1)]">
                  <h3>{title}</h3>

                  <p className="text-[var(--color-text-muted)]">
                    {description}
                  </p>
                </div>
              </Card>
            ),
          )}
        </div>
      </section>
    </Reveal>
  );
}
