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
  const horizonGuidance = [
    {
      Icon: Gauge,
      ...copy.learnPage.confidence.horizons.one,
    },
    {
      Icon: Clock3,
      ...copy.learnPage.confidence.horizons.three,
    },
    {
      Icon: Activity,
      ...copy.learnPage.confidence.horizons.six,
    },
    {
      Icon: TriangleAlert,
      ...copy.learnPage.confidence.horizons.twelve,
    },
    {
      Icon: CircleAlert,
      ...copy.learnPage.confidence.horizons.twentyFour,
    },
  ];

  return (
    <section
      aria-labelledby="forecast-horizon-guide"
      className="product-section-panel"
    >
      <div className="max-w-2xl space-y-[var(--space-2)]">
        <h2 id="forecast-horizon-guide">
          {copy.learnPage.confidence.title}
        </h2>

        <p className="text-[var(--color-text-muted)]">
          {copy.learnPage.confidence.description}
        </p>
      </div>

      <Card className="horizon-guide-card">
        <ul className="horizon-guide-list">
          {horizonGuidance.map(
            ({
              Icon,
              label,
              detail,
            }) => (
              <li
                key={label}
                className="horizon-guide-row"
              >
                <span className="horizon-guide-icon">
                  <Icon
                    aria-hidden="true"
                    size={19}
                  />
                </span>

                <div className="horizon-guide-copy">
                  <h3>{label}</h3>

                  <p>{detail}</p>
                </div>
              </li>
            ),
          )}
        </ul>
      </Card>
    </section>
  );
}
