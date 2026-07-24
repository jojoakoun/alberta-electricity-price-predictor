import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  test,
} from "vitest";

import { setLanguage } from "../i18n/language";
import { LearnPage } from "./LearnPage";

describe("LearnPage", () => {
  beforeEach(() => {
    setLanguage("en");
  });

  test("supports an understandable and honest learning flow", async () => {
    const user = userEvent.setup();

    render(<LearnPage />);

    expect(
      screen.getByRole("heading", {
        name: "Understand WattWise",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Alberta Electric System Operator (AESO)",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Models are periodically re-evaluated with newer market data/i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "How to use each forecast horizon",
      }),
    ).toBeInTheDocument();

    expect(
      screen.queryAllByRole("progressbar"),
    ).toHaveLength(0);

    expect(
      screen.getByText(
        "The displayed market price is not the same as your complete electricity bill.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByText("What can change a forecast?"),
    );

    expect(
      screen.getByText(
        /Unexpected outages, weather, demand, and market events/i,
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("tab", {
        name: "Okay time",
      }),
    );

    expect(
      screen.getByRole("tab", {
        name: "Okay time",
      }),
    ).toHaveAttribute("aria-selected", "true");

    expect(
      screen.getByText(
        "Prices are acceptable. You can use electricity if needed, although a better forecast time may be available.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "Visit the official AESO website",
      }),
    ).toHaveAttribute(
      "href",
      "https://www.aeso.ca",
    );

    expect(
      screen.getByRole("link", {
        name: "View today’s outlook",
      }),
    ).toHaveAttribute("href", "/today");
  });
});
