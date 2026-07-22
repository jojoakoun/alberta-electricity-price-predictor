import {
  CircleHelp,
  Gauge,
  Minus,
  Sparkles,
  Star,
} from "lucide-react";

import { copy } from "../../copy";
import {
  formatAlbertaDay,
  formatAlbertaTime,
  formatNumber,
} from "../../i18n/formatters";
import { isLowerPriceOpportunity } from "../../domain/today";
import { Card } from "../Card";
import { StatusBadge } from "../StatusBadge";

function requireDifference(comparison, difference) {
  if (difference === null) {
    throw new Error(
      `${comparison} requires an API-provided price difference.`,
    );
  }

  return difference;
}

export function BestTimeCard({
  bestTime,
  comparison,
  currentPriceCents,
  currentObservedAtUtc,
  priceDifferenceCents,
  forecastSourceTimeUtc,
}) {
  let eyebrow;
  let title;
  let explanation;

  switch (comparison) {
    case "forecast_lower": {
      const difference = requireDifference(
        comparison,
        priceDifferenceCents,
      );

      eyebrow =
        copy.forecast.comparison.lowerEyebrow;
      title =
        copy.forecast.comparison.lowerTitle;
      explanation = [
        copy.forecast.comparison.lowerBefore,
        formatNumber(difference),
        copy.forecast.comparison.lowerAfter,
      ].join(" ");
      break;
    }

    case "forecast_equal":
      eyebrow =
        copy.forecast.comparison.sameEyebrow;
      title =
        copy.forecast.comparison.sameTitle;
      explanation =
        copy.forecast.comparison.sameDescription;
      break;

    case "current_lower": {
      const difference = requireDifference(
        comparison,
        priceDifferenceCents,
      );

      eyebrow =
        copy.forecast.comparison.currentEyebrow;
      title =
        copy.forecast.comparison.currentTitle;
      explanation = [
        copy.forecast.comparison.currentBefore,
        formatNumber(difference),
        copy.forecast.comparison.currentAfter,
      ].join(" ");
      break;
    }

    case "unavailable":
      eyebrow =
        copy.forecast.comparison.unavailableEyebrow;
      title =
        copy.forecast.comparison.unavailableTitle;
      explanation =
        copy.forecast.comparison.unavailableDescription;
      break;
  }

  const isOpportunity = isLowerPriceOpportunity(
    comparison,
  );

  return (
    <Card
      className="today-best-card"
      data-comparison={comparison}
    >
      <div className="today-best-heading">
        <span
          className={[
            "today-best-icon",
            isOpportunity ? "" : "is-neutral",
          ].join(" ")}
        >
          {isOpportunity ? (
            <Star
              aria-hidden="true"
              data-testid="opportunity-star"
              fill="currentColor"
              size={22}
              strokeWidth={2}
            />
          ) : comparison === "forecast_equal" ? (
            <Minus
              aria-hidden="true"
              size={22}
              strokeWidth={2.5}
            />
          ) : comparison === "current_lower" ? (
            <Gauge
              aria-hidden="true"
              size={22}
              strokeWidth={2}
            />
          ) : (
            <CircleHelp
              aria-hidden="true"
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
                forecastSourceTimeUtc,
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

        {comparison === "forecast_equal" ? (
          <span className="today-best-comparison-badge">
            {copy.forecast.comparison.sameBadge}
          </span>
        ) : comparison === "current_lower" ? (
          <span className="today-best-comparison-badge">
            {copy.forecast.comparison.currentBadge}
          </span>
        ) : comparison === "unavailable" ? (
          <span className="today-best-comparison-badge">
            {copy.forecast.comparison.unavailableBadge}
          </span>
        ) : (
          <StatusBadge
            level={bestTime.recommendation}
          />
        )}
      </div>

      {currentPriceCents !== null && (
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
