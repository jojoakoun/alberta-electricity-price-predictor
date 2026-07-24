import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { TodayPage } from "./TodayPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <TodayPage />
    </QueryClientProvider>,
  );
}

const forecasts = [
  {
    horizonHours: 1,
    targetTimeUtc: "2026-07-20T02:00:00.000Z",
    targetTimeLocal: "8:00 p.m.",
    temporalWordingKey: "in_a_few_hours",
    priceCents: 2.36,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
    forecastKind: "model_forecast",
  },
  {
    horizonHours: 3,
    targetTimeUtc: "2026-07-20T04:00:00.000Z",
    targetTimeLocal: "10:00 p.m.",
    temporalWordingKey: "in_a_few_hours",
    priceCents: 2.8,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
    forecastKind: "model_forecast",
  },
  {
    horizonHours: 6,
    targetTimeUtc: "2026-07-20T07:00:00.000Z",
    targetTimeLocal: "1:00 a.m.",
    temporalWordingKey: "in_a_few_hours",
    priceCents: 1.15,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
    forecastKind: "model_forecast",
  },
  {
    horizonHours: 12,
    targetTimeUtc: "2026-07-20T13:00:00.000Z",
    targetTimeLocal: "7:00 a.m.",
    temporalWordingKey: "in_a_few_hours",
    priceCents: 1.42,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
    forecastKind: "model_forecast",
  },
  {
    horizonHours: 24,
    targetTimeUtc: "2026-07-21T01:00:00.000Z",
    targetTimeLocal: "7:00 p.m.",
    temporalWordingKey: "tomorrow_around_this_time",
    priceCents: 1.91,
    recommendation: "acceptable",
    explanationKey: "acceptable_market_risk",
    forecastKind: "persistence_reference",
  },
];

function buildTodayResponse(overrides = {}) {
  return {
    generatedAt: "2026-07-20T01:00:00.000Z",
    confidence: "high",
    stale: false,
    futureForecastStatus: "available",
    comparison: "forecast_lower",
    currentPriceCents: 2,
    currentPriceKind: "forecast",
    currentPriceSourceAtUtc:
      "2026-07-20T01:00:00.000Z",
    currentObservedAtUtc:
      "2026-07-20T01:00:00.000Z",
    priceDifferenceCents: 0.85,
    forecasts,
    bestTime: {
      horizonHours: 6,
      targetTimeUtc: "2026-07-20T07:00:00.000Z",
      targetTimeLocal: "1:00 a.m.",
      priceCents: 1.15,
      recommendation: "acceptable",
    },
    ...overrides,
  };
}

function getRequestUrl(input) {
  if (typeof input === "string") {
    return input;
  }

  if (input instanceof URL) {
    return input.pathname;
  }

  return input.url;
}

function mockTodayResponse(response) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(
    async (input) => {
      const url = getRequestUrl(input);

      if (url === "/api/v1/today") {
        return new Response(
          JSON.stringify(response),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        );
      }

      if (url === "/api/v1/now") {
        return new Response(
          JSON.stringify({
            error: {
              code: "NOW_UNAVAILABLE",
              message: "Now is unavailable.",
            },
          }),
          {
            status: 503,
            headers: {
              "Content-Type": "application/json",
            },
          },
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    },
  );
}

describe("TodayPage", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  test("renders a genuine lower-price opportunity and reveals all forecast details", async () => {
    const user = userEvent.setup();
    mockTodayResponse(buildTodayResponse());

    renderPage();

    expect(
      await screen.findByText("A lower price is forecast"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("opportunity-star"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Persistence reference"),
    ).toBeInTheDocument();

    expect(
      screen.getByTestId(
        "current-price-point",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Forecast details", {
        selector: "h2",
      }),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Forecast details",
      }),
    );

    expect(
      screen.getByText("Forecast details", {
        selector: "h2",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Persistence reference").length,
    ).toBeGreaterThan(1);
    expect(
      screen.getByTestId("best-forecast-star"),
    ).toBeInTheDocument();
    expect(
      Element.prototype.scrollIntoView,
    ).toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", {
        name: "Hide details",
      }),
    );

    expect(
      screen.queryByText("Forecast details", {
        selector: "h2",
      }),
    ).not.toBeInTheDocument();
  });

  test("renders the no-lower-price state for an equal forecast without an opportunity star", async () => {
    const user = userEvent.setup();

    mockTodayResponse(
      buildTodayResponse({
        comparison: "forecast_equal",
        currentPriceCents: 1.15,
        priceDifferenceCents: 0,
      }),
    );

    renderPage();

    expect(
      await screen.findByText(
        "Waiting is not expected to lower the price",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("opportunity-star"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("best-forecast-halo"),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Forecast details",
      }),
    );

    expect(
      screen.queryByTestId("best-forecast-star"),
    ).not.toBeInTheDocument();
  });

  test("renders the current-price-lower state without a savings claim", async () => {
    mockTodayResponse(
      buildTodayResponse({
        comparison: "current_lower",
        currentPriceCents: 0.95,
        priceDifferenceCents: 0.2,
      }),
    );

    renderPage();

    expect(
      await screen.findByText(
        "The current price is already lower",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("opportunity-star"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Possible saving"),
    ).not.toBeInTheDocument();
  });

  test("does not request Now or invent a savings claim when comparison evidence is unavailable", async () => {
    const fetchMock = mockTodayResponse(
      buildTodayResponse({
        comparison: "unavailable",
        currentPriceCents: null,
        currentObservedAtUtc: null,
        priceDifferenceCents: null,
      }),
    );

    renderPage();

    expect(
      await screen.findByText(
        "A lower price cannot be confirmed",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("opportunity-star"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Possible saving"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Best opportunity"),
    ).not.toBeInTheDocument();

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.map(([input]) =>
          getRequestUrl(input),
        ),
      ).toEqual(["/api/v1/today"]);
    });
  });


  test(
    "uses a compact note instead of a banner for moderately old forecasts",
    async () => {
      mockTodayResponse(
        buildTodayResponse({
          confidence: "moderate",
          stale: true,
        }),
      );

      renderPage();

      expect(
        await screen.findByTestId(
          "moderate-forecast-notice",
        ),
      ).toBeInTheDocument();

      expect(
        screen.queryByText(
          "Forecasts delayed",
        ),
      ).not.toBeInTheDocument();

      expect(
        screen.getByTestId(
          "current-price-point",
        ),
      ).toBeInTheDocument();
    },
  );

  test("keeps stale forecast details visible with an explicit warning", async () => {
    const user = userEvent.setup();

    mockTodayResponse(
      buildTodayResponse({
        confidence: "low",
        stale: true,
      }),
    );

    renderPage();

    expect(
      await screen.findByText("Forecasts are stale"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("A lower price is forecast"),
    ).toBeInTheDocument();
    for (const horizon of [1, 3, 6, 12, 24]) {
      expect(
        screen.getByTestId(`forecast-point-${horizon}`),
      ).toBeInTheDocument();
    }

    await user.click(
      screen.getByRole("button", {
        name: "Forecast details",
      }),
    );

    expect(
      screen.getByText("Forecast details", {
        selector: "h2",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Persistence reference").length,
    ).toBeGreaterThan(1);
    expect(
      screen.queryByText("Recommendation unavailable"),
    ).not.toBeInTheDocument();
  });

  test("keeps a future persistence reference visible without inventing an opportunity", async () => {
    const user = userEvent.setup();

    mockTodayResponse(
      buildTodayResponse({
        futureForecastStatus: "reference_only",
        comparison: "unavailable",
        priceDifferenceCents: null,
        bestTime: null,
      }),
    );

    renderPage();

    expect(
      await screen.findByText(
        /Only the \+24-hour persistence reference remains in the future/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Persistence reference"),
    ).toBeInTheDocument();
    for (const horizon of [1, 3, 6, 12, 24]) {
      expect(
        screen.getByTestId(`forecast-point-${horizon}`),
      ).toBeInTheDocument();
    }
    expect(
      screen.queryByTestId("opportunity-star"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("best-forecast-halo"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Possible saving"),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Forecast details",
      }),
    );

    expect(
      screen.getByText("Forecast details", {
        selector: "h2",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("best-forecast-star"),
    ).not.toBeInTheDocument();
  });
});
