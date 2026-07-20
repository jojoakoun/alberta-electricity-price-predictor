import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  test,
} from "vitest";

import { ProjectPage } from "./ProjectPage";

describe("ProjectPage", () => {
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
      screen.getByText("AESO market data"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Engineering principles",
      }),
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
    ).toHaveLength(2);

    expect(
      screen.getByRole("heading", {
        name: "What I learned",
      }),
    ).toBeInTheDocument();
  });
});
