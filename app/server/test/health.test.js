jest.mock("../src/repositories/prediction-run-repository");

const request = require("supertest");

const {
  getLatestSuccessfulForecastSource,
} = require("../src/repositories/prediction-run-repository");
const { createApp } = require("../src/app");

describe("Health endpoint", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns HTTP 200 when PostgreSQL is available", async () => {
    const forecastSourceAt = new Date("2026-07-18T19:00:00.000Z");

    getLatestSuccessfulForecastSource.mockResolvedValue({
      forecast_source_at: forecastSourceAt,
    });

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
      latestForecastSourceAt: "2026-07-18T19:00:00.000Z",
      dbOk: true,
    });
  });

  test("returns null when no successful worker run exists yet", async () => {
    getLatestSuccessfulForecastSource.mockResolvedValue(null);

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
      latestForecastSourceAt: null,
      dbOk: true,
    });
  });

  test("returns HTTP 503 when PostgreSQL is unavailable", async () => {
    getLatestSuccessfulForecastSource.mockRejectedValue(
      new Error("Database unavailable"),
    );

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(503);
    expect(response.body).toEqual({
      status: "error",
      latestForecastSourceAt: null,
      dbOk: false,
    });
  });
});
