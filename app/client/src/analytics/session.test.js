import {
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import {
  getAnalyticsSessionId,
} from "./session";

describe("anonymous analytics session", () => {
  beforeEach(() => {
    window.localStorage.clear();

    vi.stubGlobal(
      "crypto",
      {
        randomUUID: vi.fn(
          () => "12345678-1234-1234-1234-123456789abc",
        ),
      },
    );
  });

  test("creates and reuses one anonymous identifier", () => {
    const firstSessionId =
      getAnalyticsSessionId();

    const secondSessionId =
      getAnalyticsSessionId();

    expect(firstSessionId).toBe(
      "12345678-1234-1234-1234-123456789abc",
    );

    expect(secondSessionId).toBe(
      firstSessionId,
    );
  });
});
