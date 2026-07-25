import {
  describe,
  expect,
  test,
} from "vitest";

import {
  getLanguage,
  setLanguage,
} from "./language";

describe("setLanguage", () => {
  test("rejects an unsupported runtime language without changing state", () => {
    const originalLanguage = getLanguage();

    expect(() => setLanguage("es")).toThrow(
      "Unsupported language: es.",
    );
    expect(getLanguage()).toBe(originalLanguage);
  });
});
