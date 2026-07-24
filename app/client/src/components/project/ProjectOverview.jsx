import {
  Clock3,
  Database,
  Layers3,
  Route,
} from "lucide-react";

import { Reveal } from "../motion/Reveal";
import { Card } from "../Card";
import { copy } from "../../copy";

export function ProjectOverview() {
  const story = copy.projectPage.story;
  const highlightCopy = copy.projectPage.highlights;
  const highlights = [
    {
      Icon: Database,
      ...highlightCopy.records,
    },
    {
      Icon: Route,
      ...highlightCopy.horizons,
    },
    {
      Icon: Clock3,
      ...highlightCopy.window,
    },
    {
      Icon: Layers3,
      ...highlightCopy.system,
    },
  ];

  const storySteps = [
    story.introduction,
    story.problem,
    story.solution,
  ];

  return (
    <>
      <Reveal>
        <section
          aria-labelledby="project-story"
          className="grid gap-[var(--space-4)] lg:grid-cols-[0.75fr_1.25fr]"
        >
          <div className="space-y-[var(--space-2)]">
            <p
              className={[
                "font-semibold uppercase tracking-wide",
                "text-[var(--font-size-caption)]",
                "text-[var(--color-brand)]",
              ].join(" ")}
            >
              {story.eyebrow}
            </p>

            <h2 id="project-story">
              {story.title}
            </h2>
          </div>

          <Card className="project-interactive-card">
            <ol className="project-story-list">
              {storySteps.map((step, index) => (
                <li
                  key={step}
                  className="project-story-step project-stagger-item"
                  data-step={`0${index + 1}`}
                  style={{
                    "--item-delay": `${index * 70}ms`,
                  }}
                >
                  <p
                    className={
                      index === 0
                        ? "font-semibold"
                        : "text-[var(--color-text-muted)]"
                    }
                  >
                    {step}
                  </p>
                </li>
              ))}
            </ol>
          </Card>
        </section>
      </Reveal>

      <Reveal>
        <section
          aria-labelledby="project-highlights"
          className="project-section-panel project-section-soft"
        >
          <div className="max-w-2xl space-y-[var(--space-2)]">
            <h2 id="project-highlights">
              {highlightCopy.title}
            </h2>

            <p className="text-[var(--color-text-muted)]">
              {highlightCopy.description}
            </p>
          </div>

          <div className="grid gap-[var(--space-3)] sm:grid-cols-2 lg:grid-cols-4">
            {highlights.map(
              ({
                Icon,
                value,
                label,
              }, index) => (
                <Card
                  key={label}
                  className={[
                    "project-stagger-item",
                    "project-interactive-card",
                    "space-y-[var(--space-3)]",
                  ].join(" ")}
                  style={{
                    "--item-delay": `${index * 65}ms`,
                  }}
                >
                  <Icon
                    aria-hidden="true"
                    className="text-[var(--color-brand)]"
                    size={22}
                  />

                  <p className="project-highlight-value">
                    {value}
                  </p>

                  <p className="text-[var(--color-text-muted)]">
                    {label}
                  </p>
                </Card>
              ),
            )}
          </div>
        </section>
      </Reveal>
    </>
  );
}
