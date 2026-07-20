import {
  Check,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

import { Card } from "../Card";
import { copy } from "../../copy";

const dataItems = [
  copy.learnPage.dataSource.items.prices,
  copy.learnPage.dataSource.items.forecastPrices,
  copy.learnPage.dataSource.items.load,
  copy.learnPage.dataSource.items.public,
] as const;

export function DataSourceCard() {
  return (
    <section aria-labelledby="data-source">
      <Card className="space-y-[var(--space-5)]">
        <div
          className={[
            "flex flex-col gap-[var(--space-3)]",
            "sm:flex-row",
          ].join(" ")}
        >
          <span
            className={[
              "inline-flex h-11 w-11 shrink-0",
              "items-center justify-center",
              "rounded-[var(--radius)]",
              "bg-[var(--color-brand-surface)]",
              "text-[var(--color-brand)]",
            ].join(" ")}
          >
            <ShieldCheck
              aria-hidden="true"
              size={22}
            />
          </span>

          <div className="space-y-[var(--space-2)]">
            <h2 id="data-source">
              {copy.learnPage.dataSource.title}
            </h2>

            <h3>
              {copy.learnPage.dataSource.organization}
            </h3>

            <p className="text-[var(--color-text-muted)]">
              {copy.learnPage.dataSource.description}
            </p>
          </div>
        </div>

        <ul
          className={[
            "grid gap-[var(--space-3)]",
            "sm:grid-cols-2",
          ].join(" ")}
        >
          {dataItems.map((item) => (
            <li
              key={item}
              className={[
                "flex items-start",
                "gap-[var(--space-2)]",
              ].join(" ")}
            >
              <Check
                aria-hidden="true"
                className={[
                  "mt-0.5 shrink-0",
                  "text-[var(--color-brand)]",
                ].join(" ")}
                size={18}
                strokeWidth={2.5}
              />

              <span className="text-[var(--color-text-muted)]">
                {item}
              </span>
            </li>
          ))}
        </ul>

        <a
          className={[
            "inline-flex min-h-11 items-center",
            "gap-[var(--space-2)]",
            "font-semibold text-[var(--color-brand)]",
            "underline-offset-4 hover:underline",
          ].join(" ")}
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
