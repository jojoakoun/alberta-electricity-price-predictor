import {
  render,
  screen,
} from "@testing-library/react";
import {
  createMemoryRouter,
  RouterProvider,
} from "react-router";
import { describe, expect, test } from "vitest";

import { AppLayout } from "./AppLayout";

describe("AppLayout", () => {
  test("renders the three primary navigation destinations", () => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <p>Now content</p>,
          },
        ],
      },
    ]);

    render(<RouterProvider router={router} />);

    expect(
      screen.getAllByRole("link", { name: "Now" }).length,
    ).toBeGreaterThan(0);

    expect(
      screen.getAllByRole("link", { name: "Today" }).length,
    ).toBeGreaterThan(0);

    expect(
      screen.getAllByRole("link", { name: "Learn" }).length,
    ).toBeGreaterThan(0);
  });
});
