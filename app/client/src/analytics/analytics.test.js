import {
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

import {
  trackAnalyticsEvent,
  trackRefresh,
} from "./analytics";

describe("analytics client", () => {
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

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
      }),
    );
  });

  test("posts an anonymous page event", async () => {
    await trackAnalyticsEvent(
      "page_view",
      "now",
    );

    expect(fetch).toHaveBeenCalledTimes(1);

    const [
      path,
      request,
    ] = fetch.mock.calls[0];

    expect(path).toBe(
      "/api/v1/analytics/events",
    );

    expect(request.method).toBe("POST");

    expect(
      JSON.parse(request.body),
    ).toEqual({
      eventType: "page_view",
      page: "now",
      sessionId:
        "12345678-1234-1234-1234-123456789abc",
      appVersion: "development",
    });
  });

  test("records refresh actions", () => {
    trackRefresh("today");

    expect(fetch).toHaveBeenCalledTimes(1);
  });

  test("does not throw when analytics is unavailable", async () => {
    fetch.mockRejectedValueOnce(
      new Error("Network unavailable."),
    );

    await expect(
      trackAnalyticsEvent(
        "page_view",
        "learn",
      ),
    ).resolves.toBeUndefined();
  });
});
