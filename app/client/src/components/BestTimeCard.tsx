import {
  Gauge,
  Minus,
  Sparkles,
  Star,
} from "lucide-react";

import { copy } from "../copy";
import {
  formatAlbertaDay,
  formatAlbertaTime,
  formatNumber,
} from "../i18n/formatters";
import type { TodayBestTime } from "../types/api";
import { Card } from "./Card";
import { StatusBadge } from "./StatusBadge";

type BestTimeCardProps = {
  bestTime: TodayBestTime;
  currentPriceCents?: number;
  currentObservedAtUtc?: string;
  referenceTimeUtc: string;
};

type PriceComparison =
  | "unknown"
  | "forecast-lower"
  | "same"
  | "current-lower";

function comparePrices(
  forecastPrice: number,
  currentPrice?: number,
): PriceComparison {
  if (currentPrice === undefined) {
    return "unknown";
  }

  if (forecastPrice < currentPrice) {
    return "forecast-lower";
  }

  if (forecastPrice > currentPrice) {
    return "current-lower";
  }

  return "same";
}

export function BestTimeCard({
  bestTime,
  currentPriceCents,
  currentObservedAtUtc,
  referenceTimeUtc,
}: BestTimeCardProps) {
  const comparison = comparePrices(
    bestTime.priceCents,
    currentPriceCents,
  );

  const difference =
    currentPriceCents === undefined
      ? 0
      : Number(
          Math.abs(
            currentPriceCents
            - bestTime.priceCents,
          ).toFixed(2),
        );

  let eyebrow = copy.forecast.bestOpportunity;
  let title = copy.forecast.bestTimeTitle;
  let explanation =
    copy.forecast.bestTimeExplanation;

  if (comparison === "forecast-lower") {
    eyebrow =
      copy.forecast.comparison.lowerEyebrow;
    title =
      copy.forecast.comparison.lowerTitle;
    explanation = [
      copy.forecast.comparison.lowerBefore,
      formatNumber(difference),
      copy.forecast.comparison.lowerAfter,
    ].join(" ");
  }

  if (comparison === "same") {
    eyebrow =
      copy.forecast.comparison.sameEyebrow;
    title =
      copy.forecast.comparison.sameTitle;
    explanation =
      copy.forecast.comparison.sameDescription;
  }

  if (comparison === "current-lower") {
    eyebrow =
      copy.forecast.comparison.currentEyebrow;
    title =
      copy.forecast.comparison.currentTitle;
    explanation = [
      copy.forecast.comparison.currentBefore,
      formatNumber(difference),
      copy.forecast.comparison.currentAfter,
    ].join(" ");
  }

  return (
    <Card
      className="today-best-card"
      data-comparison={comparison}
    >
      <div className="today-best-heading">
        <span
          className={[
            "today-best-icon",
            comparison === "same"
              || comparison === "current-lower"
              ? "is-neutral"
              : "",
          ].join(" ")}
        >
          {comparison === "same" ? (
            <Minus
              aria-hidden="true"
              size={22}
              strokeWidth={2.5}
            />
          ) : comparison === "current-lower" ? (
            <Gauge
              aria-hidden="true"
              size={22}
              strokeWidth={2}
            />
          ) : (
            <Star
              aria-hidden="true"
              fill="currentColor"
              size={22}
              strokeWidth={2}
            />
          )}
        </span>

        <div>
          <p className="product-eyebrow">
            <Sparkles
              aria-hidden="true"
              size={15}
            />
            {eyebrow}
          </p>

          <h2>{title}</h2>
        </div>
      </div>

      <div className="today-best-content">
        <div className="space-y-[var(--space-3)]">
          <div>
            <p className="today-best-day">
              {formatAlbertaDay(
                bestTime.targetTimeUtc,
                referenceTimeUtc,
              )}
            </p>

            <p className="today-best-time">
              {formatAlbertaTime(
                bestTime.targetTimeUtc,
              )}
            </p>
          </div>

          <div>
            <p className="today-best-price-label">
              {copy.forecast.futurePriceLabel}
            </p>

            <p className="today-best-price">
              {formatNumber(bestTime.priceCents)}
              <span>¢/kWh</span>
            </p>
          </div>
        </div>

        {comparison === "same" ? (
          <span className="today-best-comparison-badge">
            {copy.forecast.comparison.sameBadge}
          </span>
        ) : comparison === "current-lower" ? (
          <span className="today-best-comparison-badge">
            {copy.forecast.comparison.currentBadge}
          </span>
        ) : (
          <StatusBadge
            level={bestTime.recommendation}
          />
        )}
      </div>

      {currentPriceCents !== undefined && (
        <div className="today-best-current-price">
          <div className="today-best-current-price-copy">
            <span>
              {copy.forecast.currentObservedPriceLabel}
            </span>

            {currentObservedAtUtc && (
              <small className="today-best-observed-at">
                {copy.freshness.observed}{" "}
                {formatAlbertaTime(
                  currentObservedAtUtc,
                )}
              </small>
            )}
          </div>

          <strong>
            {formatNumber(currentPriceCents)}
            {" "}¢/kWh
          </strong>
        </div>
      )}

      <p className="max-w-2xl text-[var(--color-text-muted)]">
        {explanation}
      </p>
    </Card>
  );
}
