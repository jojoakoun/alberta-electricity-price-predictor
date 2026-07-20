import { ArrowRight, RefreshCw } from "lucide-react";
import { Link } from "react-router";

import { useNowQuery } from "../api/useNowQuery";
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
      <div className="space-y-[var(--space-4)]">
        <h1>{copy.pages.now.title}</h1>

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
      <div className="space-y-[var(--space-4)]">
        <h1>{copy.pages.now.title}</h1>

        <Card className="space-y-[var(--space-3)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.states.errorTitle}
          </p>

          <Button onClick={() => void nowQuery.refetch()}>
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
    <div className="space-y-[var(--space-5)]">
      <header>
        <h1>{copy.pages.now.title}</h1>
      </header>

      {data.confidence !== "high" && (
        <DelayedBanner confidence={data.confidence} />
      )}

      {recommendationUnavailable ? (
        <Card className="space-y-[var(--space-3)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.recommendations.unavailable.defaultExplanation}
          </p>
        </Card>
      ) : (
        <RecommendationCard data={data} />
      )}

      <Link
        to="/today"
        className={[
          "group inline-flex min-h-11 items-center",
          "gap-[var(--space-2)]",
          "font-semibold text-[var(--color-brand)]",
          "underline-offset-4 hover:underline",
        ].join(" ")}
      >
        <span>{copy.pages.now.todayLink}</span>

        <ArrowRight
          aria-hidden="true"
          className={[
            "transition-transform",
            "duration-[var(--motion-duration)]",
            "ease-[var(--motion-easing)]",
            "group-hover:translate-x-1",
          ].join(" ")}
          size={18}
          strokeWidth={2}
        />
      </Link>
    </div>
  );
}
