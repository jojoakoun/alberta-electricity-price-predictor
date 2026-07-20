import {
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import {
  useRef,
  useState,
} from "react";

import { useTodayQuery } from "../api/useTodayQuery";
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
      <div className="space-y-[var(--space-4)]">
        <h1>{copy.pages.today.title}</h1>

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
      <div className="space-y-[var(--space-4)]">
        <h1>{copy.pages.today.title}</h1>

        <Card className="space-y-[var(--space-3)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.states.errorTitle}
          </p>

          <Button onClick={() => void todayQuery.refetch()}>
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
    <div className="space-y-[var(--space-5)]">
      <header className="space-y-[var(--space-2)]">
        <h1>{copy.pages.today.title}</h1>

        <p className="text-[var(--color-text-muted)]">
          {copy.pages.today.description}
        </p>
      </header>

      {data.confidence !== "high" && (
        <DelayedBanner confidence={data.confidence} />
      )}

      {data.confidence === "low" ? (
        <Card className="space-y-[var(--space-3)]">
          <StatusBadge level="unavailable" />

          <p className="text-[var(--color-text-muted)]">
            {copy.recommendations.unavailable.defaultExplanation}
          </p>
        </Card>
      ) : (
        <>
          <BestTimeCard bestTime={data.bestTime} />

          <TimelineOverview
            bestTime={data.bestTime}
            forecasts={data.forecasts}
          />

          <Button
            ref={detailsButtonRef}
            aria-controls="forecasts"
            aria-expanded={showForecasts}
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
                "duration-[var(--motion-duration)]",
                showForecasts ? "rotate-180" : "",
              ].join(" ")}
              size={18}
            />
          </Button>

          {showForecasts && (
            <div
              id="forecasts"
              ref={forecastsRef}
              className="scroll-mt-[var(--space-5)]"
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
