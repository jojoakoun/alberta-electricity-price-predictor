import {
  useEffect,
  useState,
} from "react";

import {
  Check,
  Clock3,
  Gauge,
} from "lucide-react";

import { copy } from "../../copy";

import {
  formatAlbertaHourRange,
  formatAlbertaTime,
  formatNumber,
} from "../../i18n/formatters";

import { Card } from "../Card";
import { StatusBadge } from "../StatusBadge";


function useCurrentMinute() {
  const [
    currentTime,
    setCurrentTime,
  ] = useState(
    () => new Date(),
  );

  useEffect(() => {
    const intervalId = window.setInterval(
      () => {
        setCurrentTime(
          new Date(),
        );
      },
      60 * 1000,
    );

    return () => {
      window.clearInterval(
        intervalId,
      );
    };
  }, []);

  return currentTime;
}


export function RecommendationCard({
  data,
}) {
  const { recommendation } = data;

  const currentTime = useCurrentMinute();

  const {
    kind,
    sourceAtUtc,
  } = data.price;

  return (
    <Card className="now-recommendation-card">
      <div className="space-y-[var(--space-4)]">
        <StatusBadge
          level={recommendation.level}
        />

        <div className="space-y-[var(--space-2)]">
          <p className="now-recommendation-copy">
            {
              copy.recommendations[
                recommendation.level
              ].defaultExplanation
            }
          </p>

          <p className="text-[var(--color-text-muted)]">
            {copy.context[data.contextKey]}
          </p>
        </div>

        <div className="now-action-panel">
          <span className="now-action-icon">
            <Check
              aria-hidden="true"
              size={19}
              strokeWidth={2.5}
            />
          </span>

          <p>
            {
              copy.actions[
                recommendation.actionKey
              ]
            }
          </p>
        </div>
      </div>

      <div className="now-price-panel">
        <div className="flex items-center gap-[var(--space-2)]">
          <Gauge
            aria-hidden="true"
            className="text-[var(--color-brand)]"
            size={20}
          />

          <p className="now-price-label">
            {copy.price.label}
          </p>
        </div>

        <p className="now-price-value">
          {formatNumber(data.price.value)}

          <span>
            {data.price.unit}
          </span>
        </p>

        <div
          className={[
            "grid gap-[var(--space-2)]",
            "text-[var(--font-size-caption)]",
            "text-[var(--color-text-muted)]",
          ].join(" ")}
        >
          <p className="flex items-center gap-[var(--space-2)]">
            <Clock3
              aria-hidden="true"
              size={16}
              strokeWidth={2}
            />

            <span>
              {copy.price.currentTime}
              {": "}

              <strong className="text-[var(--color-text)]">
                {formatAlbertaTime(
                  currentTime.toISOString(),
                )}
              </strong>
            </span>
          </p>

          <p
            className="now-market-hour-row"
            data-testid="market-hour-row"
          >
            <span>
              {copy.price.marketHour}
              {": "}
            </span>

            <strong className="now-market-hour-range">
              {formatAlbertaHourRange(
                sourceAtUtc,
              )}
            </strong>
          </p>

          <p>
            {copy.price.kinds[kind]}
          </p>
        </div>
      </div>
    </Card>
  );
}
