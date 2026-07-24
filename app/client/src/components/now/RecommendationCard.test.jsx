import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import {
  RecommendationCard,
} from "./RecommendationCard";


const response = {
  generatedAt:
    "2026-07-24T04:00:00.000Z",
  confidence: "high",
  stale: false,

  price: {
    value: 3.87,
    unit: "¢/kWh",
    kind: "forecast",
    sourceAtUtc:
      "2026-07-24T04:00:00.000Z",
  },

  recommendation: {
    level: "acceptable",
    explanationKey:
      "about_average",
    actionKey:
      "use_if_needed",
  },

  contextKey:
    "about_average",
};


describe("RecommendationCard", () => {
  beforeEach(() => {
    vi.useFakeTimers();

    vi.setSystemTime(
      new Date(
        "2026-07-24T04:19:00.000Z",
      ),
    );
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  test(
    "shows Alberta time, market hour, and the forecast source",
    () => {
      render(
        <RecommendationCard
          data={response}
        />,
      );

      expect(
        screen.getByText(
          "Price now",
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          "Electricity use is acceptable, but this is not the best time.",
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByText(
          /Current Alberta time/i,
        ),
      ).toHaveTextContent(
        "10:19",
      );

      const marketHourRow = screen.getByTestId(
        "market-hour-row",
      );

      expect(
        marketHourRow,
      ).toHaveTextContent(
        "Market hour: 10:00 p.m. – 11:00 p.m.",
      );

      expect(
        marketHourRow,
      ).toHaveClass(
        "now-market-hour-row",
      );

      expect(
        screen.getByText(
          "AESO estimate for the current market hour.",
        ),
      ).toBeInTheDocument();
    },
  );

  test(
    "labels a finalized current-hour price",
    () => {
      render(
        <RecommendationCard
          data={{
            ...response,

            price: {
              ...response.price,
              kind: "actual",
            },
          }}
        />,
      );

      expect(
        screen.getByText(
          "Finalized AESO price for the current market hour.",
        ),
      ).toBeInTheDocument();
    },
  );

  test(
    "labels a latest-finalized fallback honestly",
    () => {
      render(
        <RecommendationCard
          data={{
            ...response,

            price: {
              ...response.price,
              kind:
                "fallback_actual",
              sourceAtUtc:
                "2026-07-24T02:00:00.000Z",
            },
          }}
        />,
      );

      expect(
        screen.getByText(
          /Latest finalized AESO price/i,
        ),
      ).toBeInTheDocument();

      expect(
        screen.getByTestId(
          "market-hour-row",
        ),
      ).toHaveTextContent(
        "Market hour: 8:00 p.m. – 9:00 p.m.",
      );
    },
  );
});
