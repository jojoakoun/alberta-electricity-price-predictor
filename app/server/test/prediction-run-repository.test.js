jest.mock("../src/db/pool", () => ({
  pool: {
    query: jest.fn(),
  },
}));

const { pool } = require("../src/db/pool");
const {
  getLatestSuccessfulForecastSource,
} = require("../src/repositories/prediction-run-repository");

describe("Prediction run repository", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns the source market hour from the latest successful run", async () => {
    const forecastSourceAt = new Date(
      "2026-07-18T19:00:00.000Z",
    );

    pool.query.mockResolvedValue({
      rows: [
        {
          forecast_source_at: forecastSourceAt,
        },
      ],
    });

    await expect(
      getLatestSuccessfulForecastSource(),
    ).resolves.toEqual({
      forecast_source_at: forecastSourceAt,
    });

    const query = pool.query.mock.calls[0][0];

    expect(query).toContain("WHERE status = 'success'");
    expect(query).toContain("generated_at");
    expect(query).not.toContain("created_at");
  });

  test("returns null when no successful run exists", async () => {
    pool.query.mockResolvedValue({ rows: [] });

    await expect(
      getLatestSuccessfulForecastSource(),
    ).resolves.toBeNull();
  });
});
