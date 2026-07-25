import {
  render,
  screen,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  test,
} from "vitest";

import { setLanguage } from "../i18n/language";
import { ProjectPage } from "./ProjectPage";

describe("ProjectPage", () => {
  beforeEach(() => {
    setLanguage("en");
  });

  test("presents the product, engineering work, and developer", () => {
    render(<ProjectPage />);

    expect(
      screen.getByRole("heading", {
        name: "WattWise",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText("57,000+"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Hourly market records"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Forecast horizons"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("End-to-end"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "View forecasts",
      }),
    ).toHaveAttribute("href", "/today");

    expect(
      screen.getByRole("heading", {
        name: "AESO market data",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Step 06"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Engineering principles",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Explainable recommendations",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Node.js"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Joël-Hervé Akoun",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getAllByRole("link", {
        name: /LinkedIn/i,
      }),
    ).toHaveLength(1);

    expect(
      screen.getByRole("heading", {
        name: "What this project taught me",
      }),
    ).toBeInTheDocument();
  });

  test("resolves project highlights after a language change", () => {
    const { rerender } = render(<ProjectPage />);

    setLanguage("fr");
    rerender(<ProjectPage />);

    expect(
      screen.getByText("Observations horaires du marché"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Horizons de prévision"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("De bout en bout"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "Voir les prévisions",
      }),
    ).toHaveAttribute("href", "/today");

    expect(
      screen.queryByText("Hourly market records"),
    ).not.toBeInTheDocument();
  });
});
