import {
  Check,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

export function DataSourceCard() {
  const dataItems = [
    copy.learnPage.dataSource.items.prices,
    copy.learnPage.dataSource.items.forecastPrices,
    copy.learnPage.dataSource.items.load,
    copy.learnPage.dataSource.items.public,
  ] as const;
  return (
    <section aria-labelledby="data-source">
      <Card className="learn-source-card">
        <div className="learn-source-heading">
          <span className="learn-source-icon">
            <ShieldCheck
              aria-hidden="true"
              size={24}
            />
          </span>

          <div className="space-y-[var(--space-3)]">
            <h2 id="data-source">
              {copy.learnPage.dataSource.title}
            </h2>

            <h3>
              {copy.learnPage.dataSource.organization}
            </h3>

            <p className="max-w-3xl text-[var(--color-text-muted)]">
              {copy.learnPage.dataSource.description}
            </p>
          </div>
        </div>

        <ul className="learn-source-grid">
          {dataItems.map((item) => (
            <li key={item}>
              <Check
                aria-hidden="true"
                size={18}
                strokeWidth={2.5}
              />

              <span>{item}</span>
            </li>
          ))}
        </ul>

        <a
          className="product-external-link"
          href={copy.learnPage.dataSource.websiteUrl}
          rel="noreferrer"
          target="_blank"
        >
          {copy.learnPage.dataSource.websiteLabel}

          <ExternalLink
            aria-hidden="true"
            size={17}
          />
        </a>
      </Card>
    </section>
  );
}
