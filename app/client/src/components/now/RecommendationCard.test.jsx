import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import {
  afterEach,
  describe,
  expect,
  test,
} from "vitest";

import { RecommendationCard } from "./RecommendationCard";

afterEach(() => {
  cleanup();
});

const response = {
  generatedAt: "2026-07-20T15:00:00.000Z",
  confidence: "high",
  stale: false,

  price: {
    value: 1.3,
    unit: "¢/kWh",
    observedAtUtc: "2026-07-20T14:00:00.000Z",
  },

  recommendation: {
    level: "acceptable",
    explanationKey: "acceptable_market_risk",
    actionKey: "use_if_needed",
  },

  contextKey: "about_average",
};

describe("RecommendationCard", () => {
  test("labels the current observed price and shows only its observation time", () => {
    render(
      <RecommendationCard data={response} />,
    );

    expect(
      screen.getByText(/Latest observed market price/i),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Price observed at/i),
    ).toHaveTextContent("8:00");

    expect(
      screen.queryByText(/Recommendation updated/i),
    ).not.toBeInTheDocument();
  });

  test("supports responses without an observation timestamp", () => {
    render(
      <RecommendationCard
        data={{
          ...response,
          price: {
            value: response.price.value,
            unit: response.price.unit,
          },
        }}
      />,
    );

    expect(
      screen.queryByText(/Price observed at/i),
    ).not.toBeInTheDocument();

    expect(
      screen.getByText(/Latest observed market price/i),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(/Recommendation updated/i),
    ).not.toBeInTheDocument();
  });
});
