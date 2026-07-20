import {
  BookOpenCheck,
} from "lucide-react";

import { copy } from "../../copy";

export function LearnHero() {
  return (
    <header className="product-hero learn-hero">
      <div
        aria-hidden="true"
        className="product-hero-orb"
      />

      <p className="product-eyebrow product-hero-item">
        <BookOpenCheck aria-hidden="true" size={18} />
        {copy.navigation.learn}
      </p>

      <h1 className="product-page-title product-hero-item">
        {copy.learnPage.hero.title}
      </h1>

      <p className="product-hero-description product-hero-item">
        {copy.learnPage.hero.description}
      </p>

      <div className="product-chip-row product-hero-item">
        <span>{copy.learnPage.hero.chips.data}</span>
        <span>{copy.learnPage.hero.chips.forecasts}</span>
        <span>
          {copy.learnPage.hero.chips.recommendations}
        </span>
      </div>
    </header>
  );
}
