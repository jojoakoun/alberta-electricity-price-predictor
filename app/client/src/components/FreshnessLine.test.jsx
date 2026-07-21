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

import { setLanguage } from "../i18n/language";
import { FreshnessLine } from "./FreshnessLine";

afterEach(() => {
  cleanup();
  setLanguage("en");
});

describe("FreshnessLine", () => {
  test("labels the forecast source-data hour in English", () => {
    setLanguage("en");

    render(
      <FreshnessLine
        sourceDataAtUtc="2026-07-20T01:00:00.000Z"
      />,
    );

    expect(
      screen.getByText(
        /Forecasts calculated from market data up to/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Recommendation updated/i),
    ).not.toBeInTheDocument();
  });

  test("labels the forecast source-data hour in French", () => {
    setLanguage("fr");

    render(
      <FreshnessLine
        sourceDataAtUtc="2026-07-20T01:00:00.000Z"
      />,
    );

    expect(
      screen.getByText(
        /Prévisions calculées à partir des données du marché jusqu’à/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Recommandation mise à jour/i),
    ).not.toBeInTheDocument();
  });
});
