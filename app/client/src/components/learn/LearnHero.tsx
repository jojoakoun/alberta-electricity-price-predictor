import { copy } from "../../copy";

export function LearnHero() {
  return (
    <header
      className={[
        "space-y-[var(--space-3)]",
        "rounded-[var(--radius)]",
        "border border-[var(--color-border)]",
        "bg-[var(--color-surface)]",
        "p-[var(--space-4)]",
        "shadow-[var(--shadow-card)]",
        "sm:p-[var(--space-5)]",
      ].join(" ")}
    >
      <p
        className={[
          "font-semibold uppercase tracking-wide",
          "text-[var(--font-size-caption)]",
          "text-[var(--color-brand)]",
        ].join(" ")}
      >
        {copy.navigation.learn}
      </p>

      <h1
        className={[
          "text-[var(--font-size-hero)]",
          "leading-[var(--line-height-hero)]",
        ].join(" ")}
      >
        {copy.learnPage.hero.title}
      </h1>

      <p className="max-w-2xl text-[var(--color-text-muted)]">
        {copy.learnPage.hero.description}
      </p>
    </header>
  );
}
