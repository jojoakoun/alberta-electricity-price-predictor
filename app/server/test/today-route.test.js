jest.mock("../src/services/today-service", () => ({
  getToday: jest.fn(),
}));

const request = require("supertest");

const { createApp } = require("../src/app");
const { getToday } = require("../src/services/today-service");

describe("GET /api/v1/today", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns the public Today response", async () => {
    getToday.mockResolvedValue({
      generatedAt: "2026-07-18T19:00:00.000Z",
      confidence: "high",
      stale: false,
      forecasts: [],
      bestTime: null,
    });

    const response = await request(createApp()).get(
      "/api/v1/today",
    );

    expect(response.status).toBe(200);
    expect(response.body.generatedAt).toBe(
      "2026-07-18T19:00:00.000Z",
    );
  });

  test("returns the public error contract when no predictions exist", async () => {
    getToday.mockResolvedValue(null);

    const response = await request(createApp()).get(
      "/api/v1/today",
    );

    expect(response.status).toBe(404);
    expect(response.body).toEqual({
      error: {
        code: "PREDICTIONS_NOT_FOUND",
        message: "No predictions are available.",
      },
    });
  });
});
