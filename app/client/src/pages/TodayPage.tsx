import "../styles/product-pages.css";

import {
  CalendarClock,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import {
  useRef,
  useState,
} from "react";

import { useTodayQuery } from "../api/useTodayQuery";
import { useNowQuery } from "../api/useNowQuery";
import { AppReveal } from "../components/motion/AppReveal";
import { BestTimeCard } from "../components/BestTimeCard";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DelayedBanner } from "../components/DelayedBanner";
import { ForecastList } from "../components/ForecastList";
import { FreshnessLine } from "../components/FreshnessLine";
import { StatusBadge } from "../components/StatusBadge";
import { TimelineOverview } from "../components/TimelineOverview";
import { copy } from "../copy";

export function TodayPage() {
  const todayQuery = useTodayQuery();
  const nowQuery = useNowQuery();
  const forecastsRef = useRef<HTMLDivElement>(null);
  const detailsButtonRef = useRef<HTMLButtonElement>(null);
  const [showForecasts, setShowForecasts] = useState(false);

  function toggleForecasts() {
    const nextState = !showForecasts;

    setShowForecasts(nextState);

    window.setTimeout(() => {
      if (nextState) {
        forecastsRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });

        return;
      }

      detailsButtonRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 0);
  }

  if (todayQuery.isPending) {
    return (
      <div className="product-page mx-auto max-w-5xl">
        <header className="product-hero product-hero-compact">
          <p className="product-eyebrow">
            <CalendarClock aria-hidden="true" size={17} />
            {copy.pages.today.eyebrow}
          </p>

          <h1 className="product-page-title">
            {copy.pages.today.title}
          </h1>
        </header>

        <Card aria-live="polite">
          <p className="text-[var(--color-text-muted)]">
            {copy.states.loading}
          </p>
        </Card>
      </div>
    );
  }

  if (todayQuery.isError) {
    return (
      <div className="product-page mx-auto max-w-5xl">
        <header className="product-hero product-hero-compact">
          <p className="product-eyebrow">
            <CalendarClock aria-hidden="true" size={17} />
            {copy.pages.today.eyebrow}
          </p>

          <h1 className="product-page-title">
            {copy.pages.today.title}
          </h1>
        </header>

        <Card className="space-y-[var(--space-4)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.states.errorTitle}
          </p>

          <Button
            className="product-action-button"
            onClick={() => void todayQuery.refetch()}
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

  const data = todayQuery.data;

  return (
    <div
      className={[
        "product-page today-page",
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
          <CalendarClock aria-hidden="true" size={17} />
          {copy.pages.today.eyebrow}
        </p>

        <h1 className="product-page-title product-hero-item">
          {copy.pages.today.title}
        </h1>

        <p className="product-hero-description product-hero-item">
          {copy.pages.today.description}
        </p>

        <div className="product-chip-row product-hero-item">
          <span>{copy.forecast.horizons.one}</span>
          <span>{copy.forecast.horizons.three}</span>
          <span>{copy.forecast.horizons.six}</span>
          <span>{copy.forecast.horizons.twelve}</span>
          <span>{copy.forecast.horizons.twentyFour}</span>
        </div>
      </header>

      {data.confidence !== "high" && (
        <AppReveal>
          <DelayedBanner confidence={data.confidence} />
        </AppReveal>
      )}

      {data.confidence === "low" ? (
        <AppReveal>
          <Card className="space-y-[var(--space-4)]">
            <StatusBadge level="unavailable" />

            <p className="text-[var(--color-text-muted)]">
              {copy.recommendations.unavailable.defaultExplanation}
            </p>
          </Card>
        </AppReveal>
      ) : (
        <>
          <AppReveal>
            <BestTimeCard
              bestTime={data.bestTime}
              currentPriceCents={
                nowQuery.data?.price.value
              }
              currentObservedAtUtc={
                nowQuery.data?.price.observedAtUtc
              }
              referenceTimeUtc={data.generatedAt}
            />
          </AppReveal>

          <AppReveal delay={70}>
            <TimelineOverview
              bestTime={data.bestTime}
              currentPriceCents={
                nowQuery.data?.price.value
              }
              forecasts={data.forecasts}
              referenceTimeUtc={data.generatedAt}
            />
          </AppReveal>

          <AppReveal delay={110}>
            <div className="forecast-toggle-panel">
              <div>
                <h2>
                  {copy.pages.today.exploreTitle}
                </h2>

                <p>
                  {copy.pages.today.exploreDescription}
                </p>
              </div>

              <Button
                ref={detailsButtonRef}
                aria-controls="forecasts"
                aria-expanded={showForecasts}
                className="product-action-button"
                onClick={toggleForecasts}
                variant="secondary"
              >
                {showForecasts
                  ? copy.forecast.hideDetails
                  : copy.forecast.viewForecasts}

                <ChevronDown
                  aria-hidden="true"
                  className={[
                    "ml-[var(--space-2)]",
                    "transition-transform",
                    showForecasts ? "rotate-180" : "",
                  ].join(" ")}
                  size={18}
                />
              </Button>
            </div>
          </AppReveal>

          {showForecasts && (
            <div
              id="forecasts"
              ref={forecastsRef}
              className={[
                "forecast-details-reveal",
                "scroll-mt-[var(--space-5)]",
              ].join(" ")}
            >
              <ForecastList
                bestTime={data.bestTime}
                forecasts={data.forecasts}
              />
            </div>
          )}

          <FreshnessLine generatedAt={data.generatedAt} />
        </>
      )}
    </div>
  );
}
