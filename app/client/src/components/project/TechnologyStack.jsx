import { Reveal } from "../motion/Reveal";
import { copy } from "../../copy";

export function TechnologyStack() {
  const stack = copy.projectPage.stack;

  return (
    <Reveal>
      <section
        aria-labelledby="technology-stack"
        className="space-y-[var(--space-4)]"
      >
        <div className="max-w-2xl space-y-[var(--space-2)]">
          <h2 id="technology-stack">
            {stack.title}
          </h2>

          <p className="text-[var(--color-text-muted)]">
            {stack.description}
          </p>
        </div>

        <ul className="flex flex-wrap gap-[var(--space-2)]">
          {stack.technologies.map(
            (technology, index) => (
              <li
                key={technology}
                className="project-tech-pill"
                style={{
                  "--tech-delay": `${index * 32}ms`,
                }}
              >
                {technology}
              </li>
            ),
          )}
        </ul>
      </section>
    </Reveal>
  );
}
