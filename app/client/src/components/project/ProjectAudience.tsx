import { copy } from "../../copy";

export function ProjectAudience() {
  return (
    <section
      aria-labelledby="project-audience-title"
      className={[
        "relative overflow-hidden",
        "rounded-[var(--radius)]",
        "border-2 border-[var(--color-brand)]",
        "bg-[var(--color-brand-surface)]",
        "p-[var(--space-5)]",
        "shadow-[var(--shadow-card)]",
      ].join(" ")}
    >
      <div
        aria-hidden="true"
        className={[
          "absolute -right-12 -top-12",
          "h-40 w-40 rounded-full",
          "bg-[var(--color-brand)] opacity-10",
        ].join(" ")}
      />

      <div className="relative grid gap-[var(--space-4)]">
        <div className="space-y-[var(--space-2)]">
          <p className="product-eyebrow">
            {copy.audience.title}
          </p>

          <h2
            id="project-audience-title"
            className="max-w-3xl"
          >
            {copy.audience.primary}
          </h2>

          <p
            className={[
              "max-w-3xl",
              "text-[var(--color-text-muted)]",
              "leading-7",
            ].join(" ")}
          >
            {copy.audience.project}
          </p>
        </div>

        <div
          className={[
            "rounded-[var(--radius)]",
            "border border-[var(--color-okay)]",
            "bg-[var(--color-okay-surface)]",
            "p-[var(--space-4)]",
          ].join(" ")}
        >
          <h3>{copy.audience.fixedTitle}</h3>

          <p
            className={[
              "mt-[var(--space-1)]",
              "text-[var(--color-text-muted)]",
            ].join(" ")}
          >
            {copy.audience.fixedDetail}
          </p>
        </div>
      </div>
    </section>
  );
}
