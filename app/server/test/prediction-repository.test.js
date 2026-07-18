jest.mock("../src/db/pool", () => ({
  pool: {
    query: jest.fn(),
  },
}));

const { pool } = require("../src/db/pool");
const {
  getLatestFinalizedPrice,
  getLatestPredictions,
  getRecentFinalizedPrices,
} = require("../src/repositories/prediction-repository");

describe("Prediction repository", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("returns predictions from the latest successful run", async () => {
    pool.query.mockResolvedValue({
      rows: [
        {
          horizon_hours: 1,
          target_time_utc: "2026-07-18T20:00:00.000Z",
          predicted_price: "84.20",
          recommendation: "Recommended",
          explanation:
            "Predicted price is favorable compared with the recent market.",
          generated_at: "2026-07-18T19:00:00.000Z",
        },
      ],
    });

    const predictions = await getLatestPredictions();

    expect(predictions).toHaveLength(1);
    expect(predictions[0].horizon_hours).toBe(1);
    expect(pool.query).toHaveBeenCalledTimes(1);
  });

  test("returns the latest finalized market price", async () => {
    pool.query.mockResolvedValue({
      rows: [
        {
          datetime_utc: "2026-07-18T19:00:00.000Z",
          actual_price: "61.40",
        },
      ],
    });

    await expect(getLatestFinalizedPrice()).resolves.toEqual({
      datetime_utc: "2026-07-18T19:00:00.000Z",
      actual_price: "61.40",
    });
  });

  test("returns null when no finalized market price exists", async () => {
    pool.query.mockResolvedValue({ rows: [] });

    await expect(getLatestFinalizedPrice()).resolves.toBeNull();
  });

  test("loads recent finalized prices with a parameterized limit", async () => {
    pool.query.mockResolvedValue({
      rows: [{ actual_price: "20.00" }, { actual_price: "40.00" }],
    });

    const prices = await getRecentFinalizedPrices(720);

    expect(prices).toEqual([
      { actual_price: "20.00" },
      { actual_price: "40.00" },
    ]);
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining("LIMIT $1"),
      [720],
    );
  });
});
