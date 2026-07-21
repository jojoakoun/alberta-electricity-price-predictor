import {
  BrainCircuit,
  ChartNoAxesCombined,
  Database,
  PanelsTopLeft,
  Server,
  Workflow,
} from "lucide-react";

import { copy } from "../../copy";
import { Card } from "../Card";
import { Reveal } from "../motion/Reveal";

export function EngineeringJourney() {
  const journey = copy.projectPage.journey;

  const journeySteps = [
    {
      number: "01",
      Icon: Database,
      ...journey.steps.source,
    },
    {
      number: "02",
      Icon: Workflow,
      ...journey.steps.data,
    },
    {
      number: "03",
      Icon: ChartNoAxesCombined,
      ...journey.steps.features,
    },
    {
      number: "04",
      Icon: BrainCircuit,
      ...journey.steps.models,
    },
    {
      number: "05",
      Icon: Server,
      ...journey.steps.api,
    },
    {
      number: "06",
      Icon: PanelsTopLeft,
      ...journey.steps.product,
    },
  ];

  return (
    <Reveal>
      <section
        aria-labelledby="engineering-journey"
        className={[
          "project-section-panel",
          "project-journey-section",
        ].join(" ")}
      >
        <div className="max-w-2xl space-y-[var(--space-2)]">
          <h2 id="engineering-journey">
            {journey.title}
          </h2>

          <p className="text-[var(--color-text-muted)]">
            {journey.description}
          </p>
        </div>

        <div className="project-journey-boundary">
          {journey.startLabel}
        </div>

        <ol className="project-journey-timeline">
          {journeySteps.map(
            ({
              number,
              Icon,
              title,
              description,
            }, index) => (
              <li
                key={title}
                className="project-journey-step"
                style={{
                  "--step-delay":
                    `${80 + index * 75}ms`,
                }}
              >
                <span className="project-journey-node">
                  <Icon
                    aria-hidden="true"
                    size={19}
                  />
                </span>

                <Card
                  className={[
                    "project-journey-card",
                    "project-interactive-card",
                    "space-y-[var(--space-3)]",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "font-semibold uppercase tracking-wide",
                      "text-[var(--font-size-caption)]",
                      "text-[var(--color-brand)]",
                    ].join(" ")}
                  >
                    {journey.stepLabel} {number}
                  </span>

                  <h3>{title}</h3>

                  <p className="text-[var(--color-text-muted)]">
                    {description}
                  </p>
                </Card>
              </li>
            ),
          )}
        </ol>

        <div className="project-journey-boundary">
          {journey.endLabel}
        </div>
      </section>
    </Reveal>
  );
}
