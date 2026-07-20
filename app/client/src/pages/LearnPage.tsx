import { ConfidenceLevels } from "../components/learn/ConfidenceLevels";
import { DataSourceCard } from "../components/learn/DataSourceCard";
import { LearnHero } from "../components/learn/LearnHero";
import { LearningTimeline } from "../components/learn/LearningTimeline";
import { LimitationsCard } from "../components/learn/LimitationsCard";
import { RecommendationExplorer } from "../components/learn/RecommendationExplorer";

export function LearnPage() {
  return (
    <div className="space-y-[var(--space-7)]">
      <LearnHero />

      <LearningTimeline />

      <RecommendationExplorer />

      <DataSourceCard />

      <ConfidenceLevels />

      <LimitationsCard />
    </div>
  );
}
