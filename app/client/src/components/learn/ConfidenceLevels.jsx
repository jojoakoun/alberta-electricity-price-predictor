import {
  Activity,
  CircleAlert,
  Clock3,
  Gauge,
  TriangleAlert,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

export function ConfidenceLevels() {
  const confidenceHorizons = [
    {
      Icon: Gauge,
      score: 100,
      ...copy.learnPage.confidence.horizons.one,
    },
    {
      Icon: Clock3,
      score: 84,
      ...copy.learnPage.confidence.horizons.three,
    },
    {
      Icon: Activity,
      score: 70,
      ...copy.learnPage.confidence.horizons.six,
    },
    {
      Icon: TriangleAlert,
      score: 52,
      ...copy.learnPage.confidence.horizons.twelve,
    },
    {
      Icon: CircleAlert,
      score: 34,
      ...copy.learnPage.confidence.horizons.twentyFour,
    },
  ];
  return (
    <section
      aria-labelledby="forecast-confidence"
      className="product-section-panel"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="forecast-confidence">
          {copy.learnPage.confidence.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.confidence.description}
        </p>
      </div>

      <Card className="confidence-card">
        {confidenceHorizons.map(
          ({
            Icon,
            label,
            detail,
            score,
          }, index) => (
            <div
              key={label}
              className="confidence-row"
            >
              <div className="confidence-label">
                <div>
                  <Icon
                    aria-hidden="true"
                    size={19}
                  />

                  <span>{label}</span>
                </div>

                <small>{detail}</small>
              </div>

              <div
                role="progressbar"
                aria-label={`${label} relative confidence`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={score}
                className="confidence-track"
              >
                <div
                  className="confidence-fill"
                  style={{
                    "--confidence-width": `${score}%`,
                    "--confidence-delay":
                      `${120 + index * 80}ms`,
                  }}
                />
              </div>
            </div>
          ),
        )}
      </Card>
    </section>
  );
}
