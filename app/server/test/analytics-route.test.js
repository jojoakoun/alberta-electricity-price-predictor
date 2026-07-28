jest.mock(
  "../src/services/analytics-service",
  () => {
    class AnalyticsValidationError
      extends Error {}

    return {
      AnalyticsValidationError,
      recordAnalyticsEvent:
        jest.fn(),
    };
  },
);

jest.mock(
  "../src/services/private-analytics-service",
  () => ({
    getPrivateAnalytics:
      jest.fn(),
  }),
);

const request = require("supertest");

const {
  recordAnalyticsEvent,
} = require(
  "../src/services/analytics-service",
);
const {
  getPrivateAnalytics,
} = require(
  "../src/services/private-analytics-service",
);
const { createApp } = require("../src/app");

describe("analytics routes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("records one anonymous event", async () => {
    recordAnalyticsEvent.mockResolvedValue({
      id: 1,
    });

    const payload = {
      eventType: "page_view",
      page: "now",
      sessionId:
        "anonymous_session_123456",
      appVersion: "development",
    };

    const response = await request(
      createApp(),
    )
      .post("/api/v1/analytics/events")
      .send(payload);

    expect(response.status).toBe(201);
    expect(response.body).toEqual({
      recorded: true,
    });

    expect(
      recordAnalyticsEvent,
    ).toHaveBeenCalledWith(payload);
  });

  test("rejects access without the private key", async () => {
    const response = await request(
      createApp({
        analyticsPrivateKey:
          "a".repeat(32),
      }),
    ).get("/api/v1/private/analytics");

    expect(response.status).toBe(401);
  });

  test("returns analytics with the private key", async () => {
    getPrivateAnalytics.mockResolvedValue({
      totalVisits: 12,
    });

    const response = await request(
      createApp({
        analyticsPrivateKey:
          "a".repeat(32),
      }),
    )
      .get("/api/v1/private/analytics")
      .set(
        "X-Analytics-Key",
        "a".repeat(32),
      );

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      totalVisits: 12,
    });
  });
});
