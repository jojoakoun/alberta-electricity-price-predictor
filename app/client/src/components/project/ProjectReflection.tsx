import {
  Lightbulb,
} from "lucide-react";

import { Reveal } from "../motion/Reveal";
import { Card } from "../Card";
import { copy } from "../../copy";

export function ProjectReflection() {
  const reflection = copy.projectPage.reflection;
  const signature = copy.projectPage.signature;

  const [
    statement,
    ...detailParts
  ] = reflection.description.split(". ");

  const detail = detailParts.join(". ");

  return (
    <>
      <Reveal>
        <section aria-labelledby="project-reflection">
          <Card className="project-reflection">
            <Lightbulb
              aria-hidden="true"
              className="project-reflection-icon"
              size={27}
            />

            <div className="space-y-[var(--space-3)]">
              <p
                className={[
                  "font-semibold uppercase tracking-wide",
                  "text-[var(--font-size-caption)]",
                  "text-[var(--color-brand)]",
                ].join(" ")}
              >
                {reflection.eyebrow}
              </p>

              <h2 id="project-reflection">
                {reflection.title}
              </h2>

              <blockquote className="project-reflection-quote">
                “{statement}.”
              </blockquote>

              {detail && (
                <p className="max-w-3xl text-[var(--color-text-muted)]">
                  {detail.endsWith(".")
                    ? detail
                    : `${detail}.`}
                </p>
              )}
            </div>
          </Card>
        </section>
      </Reveal>

      <footer
        className={[
          "space-y-[var(--space-1)]",
          "border-t border-[var(--color-border)]",
          "pt-[var(--space-5)]",
          "text-center",
          "text-[var(--color-text-muted)]",
        ].join(" ")}
      >
        <p>{signature.label}</p>

        <p className="font-semibold text-[var(--color-text)]">
          {signature.name}
        </p>
      </footer>
    </>
  );
}
