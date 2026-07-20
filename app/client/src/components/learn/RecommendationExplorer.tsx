import { useState } from "react";

import { Card } from "../Card";
import { StatusBadge } from "../StatusBadge";
import { copy } from "../../copy";
import type { RecommendationLevel } from "../../types/recommendation";

type PublicRecommendation = Exclude<
  RecommendationLevel,
  "unavailable"
>;

const recommendationOptions = [
  {
    level: "recommended",
    title: copy.learnPage.recommendations.good.title,
    description:
      copy.learnPage.recommendations.good.description,
  },
  {
    level: "acceptable",
    title: copy.learnPage.recommendations.okay.title,
    description:
      copy.learnPage.recommendations.okay.description,
  },
  {
    level: "avoid",
    title: copy.learnPage.recommendations.wait.title,
    description:
      copy.learnPage.recommendations.wait.description,
  },
] satisfies Array<{
  level: PublicRecommendation;
  title: string;
  description: string;
}>;

export function RecommendationExplorer() {
  const [
    selectedRecommendation,
    setSelectedRecommendation,
  ] = useState<PublicRecommendation>("recommended");

  const selectedOption =
    recommendationOptions.find(
      ({ level }) =>
        level === selectedRecommendation,
    ) ?? recommendationOptions[0];

  return (
    <section
      aria-labelledby="recommendation-levels"
      className="space-y-[var(--space-4)]"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="recommendation-levels">
          {copy.learnPage.recommendations.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.recommendations.description}
        </p>
      </div>

      <div
        role="tablist"
        aria-label="Recommendation levels"
        className={[
          "grid gap-[var(--space-2)]",
          "sm:grid-cols-3",
        ].join(" ")}
      >
        {recommendationOptions.map(({ level }) => {
          const isSelected =
            level === selectedRecommendation;

          return (
            <button
              key={level}
              role="tab"
              aria-controls="recommendation-explanation"
              aria-selected={isSelected}
              className={[
                "min-h-14 rounded-[var(--radius)]",
                "border p-[var(--space-2)]",
                "text-left transition-colors",
                isSelected
                  ? [
                      "border-[var(--color-brand)]",
                      "bg-[var(--color-brand-surface)]",
                    ].join(" ")
                  : [
                      "border-[var(--color-border)]",
                      "bg-[var(--color-surface)]",
                      "hover:bg-[var(--color-brand-surface)]",
                    ].join(" "),
              ].join(" ")}
              onClick={() =>
                setSelectedRecommendation(level)
              }
              type="button"
            >
              <StatusBadge level={level} />
            </button>
          );
        })}
      </div>

      <Card
        id="recommendation-explanation"
        role="tabpanel"
        className="space-y-[var(--space-3)]"
      >
        <StatusBadge
          level={selectedRecommendation}
        />

        <h3>{selectedOption.title}</h3>

        <p className="text-[var(--color-text-muted)]">
          {selectedOption.description}
        </p>
      </Card>
    </section>
  );
}
