jest.mock("../src/db/pool", () => ({
  pool: {
    query: jest.fn(),
  },
}));

const request = require("supertest");

const { pool } = require("../src/db/pool");
const { createApp } = require("../src/app");

describe("Health endpoint", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns HTTP 200 when PostgreSQL is available", async () => {
    const forecastSourceAt = new Date("2026-07-18T19:00:00.000Z");

    pool.query.mockResolvedValue({
      rows: [{ forecast_source_at: forecastSourceAt }],
    });

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
      latestForecastSourceAt: "2026-07-18T19:00:00.000Z",
      dbOk: true,
    });

    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining("WHERE status = 'success'"),
    );
    expect(pool.query.mock.calls[0][0]).toContain("generated_at");
    expect(pool.query.mock.calls[0][0]).not.toContain("created_at");
  });

  test("returns null when no successful worker run exists yet", async () => {
    pool.query.mockResolvedValue({
      rows: [],
    });

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
      latestForecastSourceAt: null,
      dbOk: true,
    });
  });

  test("returns HTTP 503 when PostgreSQL is unavailable", async () => {
    pool.query.mockRejectedValue(new Error("Database unavailable"));

    const response = await request(createApp()).get("/api/v1/health");

    expect(response.status).toBe(503);
    expect(response.body).toEqual({
      status: "error",
      latestForecastSourceAt: null,
      dbOk: false,
    });
  });
});
