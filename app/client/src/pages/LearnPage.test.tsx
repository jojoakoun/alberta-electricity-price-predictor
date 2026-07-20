import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  test,
} from "vitest";

import { LearnPage } from "./LearnPage";

describe("LearnPage", () => {
  test("supports an understandable interactive learning flow", async () => {
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
      screen.getAllByRole("progressbar"),
    ).toHaveLength(5);

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
  });
});
