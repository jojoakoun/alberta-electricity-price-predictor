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
} from "vitest";

import {
  setLanguage,
} from "../../i18n/language";

import {
  FreshnessLine,
} from "./FreshnessLine";


describe("FreshnessLine", () => {
  beforeEach(() => {
    setLanguage("en");
  });

  afterEach(() => {
    cleanup();
  });

  test(
    "shows a compact notice for moderately old forecasts",
    () => {
      render(
        <FreshnessLine
          confidence="moderate"
          sourceDataAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      expect(
        screen.getByTestId(
          "moderate-forecast-notice",
        ),
      ).toHaveTextContent(
        "These forecasts use an older market-data hour than usual.",
      );

      expect(
        screen.getByText(
          /Forecasts calculated from market data up to/i,
        ),
      ).toHaveTextContent(
        "9:00",
      );
    },
  );

  test(
    "does not show the compact warning for fresh forecasts",
    () => {
      render(
        <FreshnessLine
          confidence="high"
          sourceDataAtUtc={
            "2026-07-20T15:00:00.000Z"
          }
        />,
      );

      expect(
        screen.queryByTestId(
          "moderate-forecast-notice",
        ),
      ).not.toBeInTheDocument();
    },
  );
});
