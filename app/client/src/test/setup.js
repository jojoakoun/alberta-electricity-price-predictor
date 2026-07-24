import "@testing-library/jest-dom/vitest";
import {
  cleanup,
} from "@testing-library/react";
import {
  afterEach,
} from "vitest";

// Remove every rendered React tree after each test.
// This prevents one language scenario from leaking into the next scenario.
afterEach(() => {
  cleanup();
});
