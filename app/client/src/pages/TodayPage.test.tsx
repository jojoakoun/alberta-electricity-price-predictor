import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  render,
  screen,
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

describe("TodayPage", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("reveals forecast details only after user action", async () => {
    const user = userEvent.setup();

    const forecasts = [1, 3, 6, 12, 24].map(
      (horizonHours, index) => ({
        horizonHours,
        targetTimeUtc:
          `2026-07-20T0${index + 1}:00:00.000Z`,
        targetTimeLocal:
          [
            "8:00 p.m.",
            "10:00 p.m.",
            "1:00 a.m.",
            "7:00 a.m.",
            "7:00 p.m.",
          ][index],
        temporalWordingKey: "in_a_few_hours",
        priceCents: [2.36, 2.8, 1.15, 1.42, 1.91][index],
        recommendation: "acceptable",
        explanationKey: "acceptable_market_risk",
      }),
    );

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          generatedAt: "2026-07-20T01:00:00.000Z",
          confidence: "high",
          stale: false,
          forecasts,
          bestTime: {
            horizonHours: 6,
            targetTimeUtc: "2026-07-20T07:00:00.000Z",
            targetTimeLocal: "1:00 a.m.",
            priceCents: 1.15,
            recommendation: "acceptable",
          },
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      ),
    );

    renderPage();

    expect(
      await screen.findByText("Best forecast time"),
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
});
