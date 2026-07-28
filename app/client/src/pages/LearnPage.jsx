import "../styles/learn.css";

import {
  usePageAnalytics,
} from "../analytics/usePageAnalytics";

import { AudienceNotice } from "../components/learn/AudienceNotice";
import { ConfidenceLevels } from "../components/learn/ConfidenceLevels";
import { DataSourceCard } from "../components/learn/DataSourceCard";
import { LearnCallToAction } from "../components/learn/LearnCallToAction";
import { LearnHero } from "../components/learn/LearnHero";
import { LearningTimeline } from "../components/learn/LearningTimeline";
import { LimitationsCard } from "../components/learn/LimitationsCard";
import { RecommendationExplorer } from "../components/learn/RecommendationExplorer";
import { AppReveal } from "../components/motion/AppReveal";

export function LearnPage() {
  usePageAnalytics("learn");

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

      <AppReveal delay={140}>
        <LearnCallToAction />
      </AppReveal>
    </div>
  );
}
