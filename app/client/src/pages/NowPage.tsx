import "../styles/product-pages.css";

import {
  ArrowRight,
  RefreshCw,
  Zap,
} from "lucide-react";
import { Link } from "react-router";

import { useNowQuery } from "../api/useNowQuery";
import { AppReveal } from "../components/motion/AppReveal";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DelayedBanner } from "../components/DelayedBanner";
import { RecommendationCard } from "../components/RecommendationCard";
import { StatusBadge } from "../components/StatusBadge";
import { copy } from "../copy";

export function NowPage() {
  const nowQuery = useNowQuery();

  if (nowQuery.isPending) {
    return (
      <div className="product-page mx-auto max-w-5xl">
        <header className="product-hero product-hero-compact">
          <p className="product-eyebrow">
            <Zap aria-hidden="true" size={17} />
            {copy.pages.now.eyebrow}
          </p>

          <h1 className="product-page-title">
            {copy.pages.now.title}
          </h1>

          <p className="product-hero-description">
            {copy.pages.now.description}
          </p>
        </header>

        <Card aria-live="polite">
          <p className="text-[var(--color-text-muted)]">
            {copy.states.loading}
          </p>
        </Card>
      </div>
    );
  }

  if (nowQuery.isError) {
    return (
      <div className="product-page mx-auto max-w-5xl">
        <header className="product-hero product-hero-compact">
          <p className="product-eyebrow">
            <Zap aria-hidden="true" size={17} />
            {copy.pages.now.eyebrow}
          </p>

          <h1 className="product-page-title">
            {copy.pages.now.title}
          </h1>
        </header>

        <Card className="space-y-[var(--space-4)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.states.errorTitle}
          </p>

          <Button
            className="product-action-button"
            onClick={() => void nowQuery.refetch()}
          >
            <RefreshCw
              aria-hidden="true"
              className="mr-[var(--space-2)]"
              size={18}
            />
            {copy.states.retry}
          </Button>
        </Card>
      </div>
    );
  }

  const data = nowQuery.data;
  const recommendationUnavailable = data.confidence === "low";

  return (
    <div
      className={[
        "product-page now-page",
        "mx-auto max-w-5xl",
        "space-y-[var(--space-7)]",
      ].join(" ")}
    >
      <header className="product-hero product-hero-compact">
        <div
          aria-hidden="true"
          className="product-hero-orb"
        />

        <p className="product-eyebrow product-hero-item">
          <Zap aria-hidden="true" size={17} />
          {copy.pages.now.eyebrow}
        </p>

        <h1 className="product-page-title product-hero-item">
          {copy.pages.now.title}
        </h1>

        <p className="product-hero-description product-hero-item">
          {copy.pages.now.description}
        </p>
      </header>

{data.confidence !== "high" && (
        <AppReveal>
          <DelayedBanner confidence={data.confidence} />
        </AppReveal>
      )}

      <AppReveal delay={60}>
        {recommendationUnavailable ? (
          <Card className="space-y-[var(--space-4)]">
            <StatusBadge level="unavailable" />

            <p className="text-[var(--color-text-muted)]">
              {copy.recommendations.unavailable.defaultExplanation}
            </p>
          </Card>
        ) : (
          <RecommendationCard data={data} />
        )}
      </AppReveal>

      <AppReveal delay={110}>
        <Link
          aria-label={copy.pages.now.todayLink}
          to="/today"
          className="product-link-card"
        >
          <span>
            <strong>{copy.pages.now.todayLink}</strong>

            <small>
              {copy.pages.now.todayLinkDescription}
            </small>
          </span>

          <ArrowRight
            aria-hidden="true"
            size={20}
            strokeWidth={2}
          />
        </Link>
      </AppReveal>
    </div>
  );
}
