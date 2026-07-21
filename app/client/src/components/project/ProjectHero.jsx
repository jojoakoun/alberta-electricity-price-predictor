import {
  ArrowUpRight,
  Sparkles,
} from "lucide-react";

import { copy } from "../../copy";

export function ProjectHero() {
  const hero = copy.projectPage.hero;

  return (
    <header
      className={[
        "project-hero",
        "grid gap-[var(--space-5)]",
        "overflow-hidden",
        "rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "p-[var(--space-4)]",
        "shadow-[var(--shadow-card)]",
        "sm:p-[var(--space-6)]",
        "lg:grid-cols-[minmax(0,1.6fr)_minmax(16rem,0.8fr)]",
        "lg:items-end",
      ].join(" ")}
    >
      <div
        aria-hidden="true"
        className="project-hero-orb"
      />

      <div className="relative z-10 space-y-[var(--space-6)]">
        <p
          className={[
            "project-hero-item",
            "project-hero-eyebrow",
            "inline-flex items-center gap-[var(--space-2)]",
            "font-semibold uppercase tracking-wide",
            "text-[var(--font-size-caption)]",
            "text-[var(--color-brand)]",
          ].join(" ")}
          style={{
            "--hero-delay": "40ms",
          }}
        >
          <Sparkles aria-hidden="true" size={16} />
          {hero.eyebrow}
        </p>

        <div className="max-w-3xl space-y-[var(--space-4)]">
          <h1
            className="project-hero-item project-hero-title"
            style={{
              "--hero-delay": "100ms",
            }}
          >
            {hero.title}
          </h1>

          <p
            className={[
              "project-hero-item",
              "project-hero-description",
              "max-w-2xl",
              "text-[var(--font-size-h3)]",
              "leading-relaxed",
              "text-[var(--color-text-muted)]",
            ].join(" ")}
            style={{
              "--hero-delay": "160ms",
            }}
          >
            {hero.description}
          </p>

          <div
            aria-label="Project disciplines"
            className={[
              "project-hero-item",
              "flex flex-wrap gap-[var(--space-2)]",
            ].join(" ")}
            style={{
              "--hero-delay": "220ms",
            }}
          >
            <span className="project-hero-chip">
              {hero.disciplines.data}
            </span>

            <span className="project-hero-chip">
              {hero.disciplines.machineLearning}
            </span>

            <span className="project-hero-chip">
              {hero.disciplines.product}
            </span>
          </div>
        </div>
      </div>

      <aside
        className={[
          "project-hero-aside",
          "relative z-10",
          "space-y-[var(--space-4)]",
          "rounded-[var(--radius)]",
          "border border-[var(--color-brand)]/20",
          "bg-[var(--color-brand-surface)]",
          "p-[var(--space-5)]",
        ].join(" ")}
        style={{
          "--hero-delay": "240ms",
        }}
      >
        <p className="text-[var(--color-text-muted)]">
          {hero.byline}
        </p>

        <p className="text-[var(--font-size-h2)] font-semibold">
          {hero.developer}
        </p>

        <a
          className="project-link-button"
          href={hero.linkedInUrl}
          rel="noreferrer"
          target="_blank"
        >
          {hero.linkedInLabel}

          <ArrowUpRight
            aria-hidden="true"
            size={18}
          />
        </a>
      </aside>
    </header>
  );
}
