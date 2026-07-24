import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import { MemoryRouter } from "react-router";
import {
  afterEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import { NowPage } from "./NowPage";

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
      <MemoryRouter>
        <NowPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("NowPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  test("renders the current recommendation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          generatedAt: "2026-07-18T19:00:00.000Z",
          confidence: "high",
          stale: false,
          price: {
            value: 8.42,
            unit: "¢/kWh",
            kind: "forecast",
            sourceAtUtc:
              "2026-07-18T19:00:00.000Z",
          },
          recommendation: {
            level: "recommended",
            explanationKey: "lower_than_usual",
            actionKey: "run_heavy_appliances",
          },
          contextKey: "lower_than_usual",
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
      await screen.findByText("Good time"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("8.42"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("¢/kWh"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "See today's forecast",
      }),
    ).toHaveAttribute("href", "/today");
  });

  test("keeps a stale observed-price recommendation visible with a warning", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          generatedAt: "2026-07-18T15:00:00.000Z",
          confidence: "low",
          stale: true,
          price: {
            value: 8.42,
            unit: "¢/kWh",
            kind: "fallback_actual",
            sourceAtUtc:
              "2026-07-18T15:00:00.000Z",
          },
          recommendation: {
            level: "recommended",
            explanationKey: "lower_than_usual",
            actionKey: "run_heavy_appliances",
          },
          contextKey: "lower_than_usual",
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
      await screen.findByText("Observed price is stale"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Good time"),
    ).toBeInTheDocument();
    expect(screen.getByText("8.42")).toBeInTheDocument();
    expect(
      screen.getByTestId(
        "market-hour-row",
      ),
    ).toHaveTextContent(
      /Market hour: 9:00 a\.m\. – 10:00 a\.m\./,
    );
    expect(
      screen.queryByText("Recommendation unavailable"),
    ).not.toBeInTheDocument();
  });
});
