import "../styles/product-pages.css";
import { AudienceNotice } from "../components/AudienceNotice";

import { AppReveal } from "../components/motion/AppReveal";
import { ConfidenceLevels } from "../components/learn/ConfidenceLevels";
import { DataSourceCard } from "../components/learn/DataSourceCard";
import { LearnHero } from "../components/learn/LearnHero";
import { LearningTimeline } from "../components/learn/LearningTimeline";
import { LimitationsCard } from "../components/learn/LimitationsCard";
import { RecommendationExplorer } from "../components/learn/RecommendationExplorer";

export function LearnPage() {
  return (
    <div
      className={[
        "product-page learn-page",
        "space-y-[var(--space-7)]",
      ].join(" ")}
    >
      <LearnHero />

      <AppReveal delay={30}>
        <AudienceNotice />
      </AppReveal>

      <AppReveal>
        <LearningTimeline />
      </AppReveal>

      <AppReveal delay={60}>
        <RecommendationExplorer />
      </AppReveal>

      <AppReveal delay={80}>
        <DataSourceCard />
      </AppReveal>

      <AppReveal delay={100}>
        <ConfidenceLevels />
      </AppReveal>

      <AppReveal delay={120}>
        <LimitationsCard />
      </AppReveal>
    </div>
  );
}
