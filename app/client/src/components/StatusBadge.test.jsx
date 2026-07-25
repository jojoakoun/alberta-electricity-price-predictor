import {
  render,
  screen,
} from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  test.each([
    ["recommended", "Good time"],
    ["acceptable", "Okay time"],
    ["avoid", "Better to wait"],
    ["unavailable", "Recommendation unavailable"],
  ])(
    "renders the %s label",
    (level, expectedLabel) => {
      render(<StatusBadge level={level} />);

      expect(
        screen.getByText(expectedLabel),
      ).toBeInTheDocument();
    },
  );
});
