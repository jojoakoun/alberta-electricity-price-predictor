import {
  ArrowRight,
} from "lucide-react";

import { copy } from "../../copy";

export function LearnCallToAction() {
  return (
    <section
      aria-labelledby="learn-next-step"
      className="learn-cta"
    >
      <div className="space-y-[var(--space-2)]">
        <p className="product-eyebrow">
          {copy.learnPage.cta.eyebrow}
        </p>

        <h2 id="learn-next-step">
          {copy.learnPage.cta.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.cta.description}
        </p>
      </div>

      <a
        className="learn-cta-link"
        href="/today"
      >
        {copy.learnPage.cta.label}

        <ArrowRight
          aria-hidden="true"
          size={18}
        />
      </a>
    </section>
  );
}
